import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from pipeline.config_loader import load_config
from pipeline.logger import get_logger
from pipeline.schemas import Conversation, ConversationTurn
from pipeline.storage import StorageEngine

logger = get_logger("Stage03_Conversations")



def _parse_ts(ts_str: str) -> Optional[datetime]:
    if not ts_str:
        return None
    try:
        # Standard ISO or Twitter timestamp
        ts_clean = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_clean)
    except Exception:
        return None


def build_conversations(rows: Optional[List[Dict]] = None, config: Optional[Dict] = None) -> List[Dict]:
    cfg = config or load_config()
    storage = StorageEngine(cfg)
    parquet_path = storage.get_parquet_path("raw_cases.parquet", subfolder="parquet")

    total_records_input = len(rows) if rows else "raw_cases.parquet"
    logger.info(f"Reconstructing multi-turn conversation threads out-of-core across {total_records_input}...")

    import duckdb
    import pyarrow as pa
    con = duckdb.connect()

    if rows:
        cleaned_rows = []
        for r in rows:
            r_copy = dict(r)
            if "metadata" in r_copy and isinstance(r_copy["metadata"], dict):
                r_copy["metadata"] = json.dumps(r_copy["metadata"]) if r_copy["metadata"] else None
            if "in_response_to_tweet_id" not in r_copy or r_copy["in_response_to_tweet_id"] is None:
                r_copy["in_response_to_tweet_id"] = None
            cleaned_rows.append(r_copy)
        con.register("raw_nodes_df", pa.Table.from_pylist(cleaned_rows))
        con.execute("""
        CREATE VIEW raw_nodes_view AS 
        SELECT 
            row_number() OVER() AS row_id,
            replace(case_id, 'TW-', '') AS tweet_id,
            customer_id,
            channel,
            coalesce(area, 'Global') AS area,
            timestamp,
            raw_text,
            coalesce(clean_text, raw_text) AS clean_text,
            inbound,
            source_type,
            in_response_to_tweet_id,
            CASE 
                WHEN in_response_to_tweet_id IS NULL OR lower(trim(cast(in_response_to_tweet_id as VARCHAR))) IN ('', 'none', 'nan') THEN NULL
                ELSE split_part(trim(cast(in_response_to_tweet_id as VARCHAR)), '.', 1)
            END AS parent_id
        FROM raw_nodes_df
        """)



    elif os.path.exists(parquet_path):
        _abs = os.path.abspath(parquet_path).replace('\\', '/')
        parquet_arg = f"'{_abs}'"
        con.execute(f"""
        CREATE VIEW raw_nodes_view AS 
        SELECT 
            row_number() OVER() AS row_id,
            replace(case_id, 'TW-', '') AS tweet_id,
            customer_id,
            channel,
            coalesce(area, 'Global') AS area,
            timestamp,
            raw_text,
            coalesce(clean_text, raw_text) AS clean_text,
            inbound,
            source_type,
            in_response_to_tweet_id,
            CASE 
                WHEN in_response_to_tweet_id IS NULL OR lower(trim(cast(in_response_to_tweet_id as VARCHAR))) IN ('', 'none', 'nan') THEN NULL
                ELSE split_part(trim(cast(in_response_to_tweet_id as VARCHAR)), '.', 1)
            END AS parent_id
        FROM {parquet_arg}
        """)

    else:
        logger.error("No raw cases parquet found and no rows passed to build_conversations.")
        return []

    rel = con.sql("SELECT * FROM raw_nodes_view ORDER BY row_id")
    cols = [c.lower() for c in rel.columns]
    nodes_list = rel.fetchall()
    col_idx = {c: i for i, c in enumerate(cols)}




    parent_map: Dict[str, List[tuple]] = {}
    for r_tuple in nodes_list:
        p_id = r_tuple[col_idx["parent_id"]]
        if p_id:
            if p_id not in parent_map:
                parent_map[p_id] = []
            parent_map[p_id].append(r_tuple)

    processed_tweets = set()
    conversations: List[Dict] = []
    chunk_to_write: List[Dict] = []
    total_conv_count = 0

    def _conv_generator():
        nonlocal chunk_to_write, total_conv_count
        for r_tuple in nodes_list:
            t_id = r_tuple[col_idx["tweet_id"]]
            if not t_id or t_id in processed_tweets:
                continue

            thread_turns: List[ConversationTurn] = []
            curr_nodes = [r_tuple]

            while curr_nodes:
                next_nodes = []
                for node in curr_nodes:
                    node_id = node[col_idx["tweet_id"]]
                    if node_id in processed_tweets:
                        continue
                    processed_tweets.add(node_id)

                    author = str(node[col_idx["customer_id"]])
                    is_inb = bool(node[col_idx["inbound"]])
                    role = "customer" if is_inb else "company"
                    raw_text = str(node[col_idx["raw_text"]] or "")
                    clean = str(node[col_idx["clean_text"]] or raw_text)

                    turn = ConversationTurn(
                        turn_id=node_id,
                        role=role,
                        author_id=author,
                        text=clean,
                        raw=raw_text,
                        timestamp=str(node[col_idx["timestamp"]] or ""),
                        in_response_to_tweet_id=str(node[col_idx["in_response_to_tweet_id"]]) if node[col_idx["in_response_to_tweet_id"]] else None
                    )
                    thread_turns.append(turn)

                    if node_id in parent_map:
                        next_nodes.extend(parent_map[node_id])
                curr_nodes = next_nodes

            if thread_turns:
                thread_turns.sort(key=lambda t: t.timestamp or "")

                cust_turns = [t for t in thread_turns if t.role == "customer"]
                comp_turns = [t for t in thread_turns if t.role == "company"]

                start_ts_str = thread_turns[0].timestamp
                end_ts_str = thread_turns[-1].timestamp
                start_dt = _parse_ts(start_ts_str)
                end_dt = _parse_ts(end_ts_str)

                duration = (end_dt - start_dt).total_seconds() if (start_dt and end_dt) else 0.0

                first_resp_time = None
                if comp_turns and start_dt:
                    comp_dt = _parse_ts(comp_turns[0].timestamp)
                    if comp_dt:
                        first_resp_time = max((comp_dt - start_dt).total_seconds(), 0.0)

                conv_id = f"CONV-{thread_turns[0].turn_id}"
                has_comp_resp = len(comp_turns) > 0
                repeat_contact = len(cust_turns) > 1

                import re
                company_handle = None
                company_handle_source = None
                
                if comp_turns:
                    comp_id = comp_turns[0].author_id
                    if comp_id.startswith("BRAND-"):
                        comp_id = comp_id[6:]
                    company_handle = comp_id
                    company_handle_source = "confirmed"
                elif cust_turns:
                    match = re.search(r"@([A-Za-z0-9_]+)", cust_turns[0].raw)
                    if match:
                        company_handle = match.group(1)
                        company_handle_source = "inferred"

                conv = Conversation(
                    conversation_id=conv_id,
                    customer_id=thread_turns[0].author_id,
                    channel=str(r_tuple[col_idx["channel"]] or "twitter"),
                    area=str(r_tuple[col_idx["area"]] or "Global"),
                    turns=thread_turns,
                    customer_turn_count=len(cust_turns),
                    company_turn_count=len(comp_turns),
                    start_time=start_ts_str,
                    end_time=end_ts_str,
                    first_response_time=first_resp_time,
                    conversation_duration=duration,
                    repeat_contact_signals=repeat_contact,
                    has_company_response=has_comp_resp,
                    company_handle=company_handle,
                    company_handle_source=company_handle_source,
                    source_type=str(r_tuple[col_idx["source_type"]] or "twcs_case"),
                    metadata={"root_tweet_id": thread_turns[0].turn_id}
                )
                conv_dict = conv.model_dump()
                chunk_to_write.append(conv_dict)
                total_conv_count += 1

                if rows and len(conversations) < 50000:
                    conversations.append(conv_dict)

                if len(chunk_to_write) >= 50000:
                    yield chunk_to_write
                    chunk_to_write = []

        if chunk_to_write:
            yield chunk_to_write
            chunk_to_write = []

    storage.write_parquet_chunks(_conv_generator(), "conversations.parquet", subfolder="conversations")
    storage.checkpoint_mgr.save_checkpoint("stage03_conversations", {"count": total_conv_count})

    logger.info(f"[STAGE 3 CONVERSATIONS] Reconstructed {total_conv_count:,} conversation threads out-of-core.")
    return conversations if rows else None




if __name__ == "__main__":
    from stage01_raw_data import generate_raw_complaints
    from stage02_clean import clean_batch
    raw = clean_batch(generate_raw_complaints(20))
    convs = build_conversations(raw)
    print(f"Built {len(convs)} conversations. First item:")
    print(convs[0])
