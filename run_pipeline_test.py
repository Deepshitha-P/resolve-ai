import os
import sys
import time
import csv
from typing import Dict, List, Any

# Ensure pipeline directory is in Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pipeline"))

from config_loader import load_config
from stage01_raw_data import load_and_ingest_raw_data
from stage02_clean import clean_batch
from stage03_conversations import build_conversations
from stage04_nlp import enrich_with_nlp

def run_pipeline():
    start_time = time.time()
    
    # 1. Load configuration and override storage paths to isolate sample_1000 run
    print("Loading config...")
    config = load_config()
    
    # Isolate intermediate parquets and checkpoints to prevent overwriting full dataset files
    config["dataset"]["raw_csv_path"] = "data/sample_1000.csv"
    config["storage"]["base_dir"] = "data/sample_1000_run"
    config["storage"]["parquet_dir"] = "data/sample_1000_run/parquet"
    config["storage"]["conversations_dir"] = "data/sample_1000_run/conversations"
    config["storage"]["nlp_dir"] = "data/sample_1000_run/nlp"
    config["storage"]["analytics_dir"] = "data/sample_1000_run/analytics"
    config["storage"]["knowledge_dir"] = "data/sample_1000_run/knowledge"
    config["storage"]["checkpoints_dir"] = "data/sample_1000_run/checkpoints"

    # Step 1: Read the original sample csv to verify traceability
    original_rows = []
    with open("data/sample_1000.csv", "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for r in reader:
            original_rows.append(r)
            
    print(f"Loaded {len(original_rows)} original rows from sample_1000.csv")

    # Step 2: Execute Pipeline Stages
    t_ingest_start = time.time()
    raw_cases = load_and_ingest_raw_data(config=config, limit=None, use_synthetic=False)
    t_ingest = time.time() - t_ingest_start
    print(f"Stage 1 Ingested: {len(raw_cases)} cases in {t_ingest:.4f}s")
    
    t_clean_start = time.time()
    cleaned = clean_batch(raw_cases)
    t_clean = time.time() - t_clean_start
    print(f"Stage 2 Cleaned: {len(cleaned)} cases in {t_clean:.4f}s")
    
    t_conv_start = time.time()
    conversations = build_conversations(cleaned, config=config)
    t_conv = time.time() - t_conv_start
    print(f"Stage 3 Conversations: {len(conversations)} threads in {t_conv:.4f}s")
    
    t_nlp_start = time.time()
    conversations_enriched = enrich_with_nlp(conversations, config=config)
    t_nlp = time.time() - t_nlp_start
    print(f"Stage 4 NLP Enriched: {len(conversations_enriched)} threads in {t_nlp:.4f}s")
    
    total_pipeline_time = time.time() - start_time
    print(f"Total processing time: {total_pipeline_time:.4f}s")

    # Step 3: Preserving row-level traceability
    print("Mapping conversation-level NLP results back to source rows...")
    
    case_map = {r["case_id"].replace("TW-", ""): r for r in cleaned}
    
    tweet_to_conv = {}
    for conv in conversations_enriched:
        nlp_data = conv.get("nlp") or {}
        for turn in conv.get("turns", []):
            t_id = turn["turn_id"]
            tweet_to_conv[t_id] = {
                "conversation_id": conv["conversation_id"],
                "nlp": nlp_data
            }

    processed_rows = []
    nlp_success_count = 0
    nlp_failure_count = 0
    
    for orig in original_rows:
        t_id = orig.get("tweet_id", "").strip()
        
        # Clean text lookup
        clean_txt = ""
        case_record = case_map.get(t_id)
        if case_record:
            clean_txt = case_record.get("clean_text") or ""
            
        # Conv & NLP lookup
        conv_info = tweet_to_conv.get(t_id, {})
        conv_id = conv_info.get("conversation_id", "")
        nlp = conv_info.get("nlp", {})
        
        if nlp:
            nlp_success_count += 1
            severity = nlp.get("severity") or {}
            severity_label = severity.get("label", "")
            severity_score = severity.get("score", "")
            escalation_signals = ",".join(nlp.get("escalation_signals", []))
            temporal_signals = ",".join(nlp.get("temporal_signals", []))
        else:
            nlp_failure_count += 1
            severity_label = ""
            severity_score = ""
            escalation_signals = ""
            temporal_signals = ""

        row_data = {
            "tweet_id": t_id,
            "author_id": orig.get("author_id", ""),
            "inbound": orig.get("inbound", ""),
            "created_at": orig.get("created_at", ""),
            "text": orig.get("text", ""),
            "response_tweet_id": orig.get("response_tweet_id", ""),
            "in_response_to_tweet_id": orig.get("in_response_to_tweet_id", ""),
            "clean_text": clean_txt,
            "conversation_id": conv_id,
            "nlp_intent": nlp.get("intent", ""),
            "nlp_category": nlp.get("category", ""),
            "nlp_subcategory": nlp.get("subcategory") or "",
            "nlp_sentiment": nlp.get("sentiment", 0.0),
            "nlp_sentiment_label": nlp.get("sentiment_label", ""),
            "nlp_emotion": nlp.get("emotion", ""),
            "nlp_urgency": nlp.get("urgency", ""),
            "nlp_severity_label": severity_label,
            "nlp_severity_score": severity_score,
            "nlp_confidence": nlp.get("confidence", ""),
            "nlp_human_review_required": nlp.get("human_review_required", False),
            "nlp_escalation_signals": escalation_signals,
            "nlp_temporal_signals": temporal_signals,
        }
        processed_rows.append(row_data)

    # Step 4: Save output to CSV
    processed_dir = "data/processed"
    os.makedirs(processed_dir, exist_ok=True)
    output_path = os.path.join(processed_dir, "sample_1000_processed.csv")
    
    headers = list(processed_rows[0].keys())
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(processed_rows)
        
    print(f"Processed output successfully saved to {output_path}")

    # Compile Validation Stats
    total_original = len(original_rows)
    total_processed = len(processed_rows)
    removed_rows = total_original - total_processed
    
    # Calculate duplicates and missing in original
    seen_ids = set()
    dup_count = 0
    missing_count = 0
    for r in original_rows:
        tid = r.get("tweet_id", "").strip()
        if not tid:
            missing_count += 1
            continue
        if tid in seen_ids:
            dup_count += 1
        seen_ids.add(tid)

    # Calculate distributions from row levels
    sentiments = {}
    intents = {}
    categories = {}
    severities = {}
    
    for r in processed_rows:
        s_lbl = r["nlp_sentiment_label"] or "unknown"
        sentiments[s_lbl] = sentiments.get(s_lbl, 0) + 1
        
        intent = r["nlp_intent"] or "unknown"
        intents[intent] = intents.get(intent, 0) + 1
        
        cat = r["nlp_category"] or "unknown"
        categories[cat] = categories.get(cat, 0) + 1
        
        sev = r["nlp_severity_label"] or "unknown"
        severities[sev] = severities.get(sev, 0) + 1

    print("\n" + "="*50)
    print("VALIDATION REPORT (1,000 Row Run)")
    print("="*50)
    print(f"1. Original rows = {total_original}")
    print(f"2. Rows successfully processed = {total_processed}")
    print(f"3. Rows removed = {removed_rows}")
    print(f"4. Duplicate count = {dup_count}")
    print(f"5. Missing/invalid records = {missing_count}")
    print(f"6. NLP processing success count = {nlp_success_count}")
    print(f"7. NLP processing failure count = {nlp_failure_count}")
    print(f"8. Processing time = {total_pipeline_time:.4f} seconds")
    print(f"9. Output file location = {os.path.abspath(output_path)}")
    print(f"10. List of final columns = {headers}")
    print(f"11. Number of unique conversations/cases = {len(conversations_enriched)}")
    print(f"12. Number of records by sentiment = {sentiments}")
    print(f"13. Number of records by intent = {intents}")
    print(f"14. Number of records by topic/category = {categories}")
    print(f"15. Number of records by severity = {severities}")
    print("="*50 + "\n")

    # Scalability Analysis (Estimates based on 1,000 rows run)
    est_50k_time_sec = total_pipeline_time * 50
    est_50k_time_min = est_50k_time_sec / 60
    
    print("="*50)
    print("SCALABILITY ESTIMATES FOR 50K+ ROWS (Based on 1,000 rows run)")
    print("="*50)
    print(f"- Deterministic pipeline: YES (the local NLP and rule-based clustering run deterministically)")
    print(f"- Approximate processing time for 1,000 rows: {total_pipeline_time:.2f} seconds")
    print(f"- Estimated processing time for 50K rows: {est_50k_time_sec:.2f} seconds ({est_50k_time_min:.2f} minutes) [ESTIMATE]")
    print(f"- Memory-heavy stages: Stage 3 (build_conversations: building parent-child map in-memory), Stage 7 (cluster_issues: matrix operations for clustering)")
    print(f"- Likely bottlenecks: In-memory dictionary traversal during thread threading, TF-IDF embeddings vectorization for large datasets")
    print(f"- Is batching needed: Recommended for conversation building and NLP stages when scaling above 100K rows")
    print(f"- NLP inference batching: Yes, can be batched if migrating to model-based deep learning, but the current local rule-based NLP runs in O(N) very quickly")
    print(f"- Intermediate output persistence: Already supported via Parquet checkpoints in StorageEngine")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_pipeline()
