"""
stage05_analytics.py ΓÇö Change 1 & 2 surgical additions:
  ΓÇó compute_prt_analytics(): groups by (product, region, topic) triple and
    computes trajectory aggregates (avg_start, avg_end, avg_delta,
    escalation_rate, recovery_rate, avg_csat_proxy, resolution_rate).
  ΓÇó by_product_region_topic dict added to the top-level analytics summary.
  ΓÇó Existing by_category / by_intent etc. are preserved for backward compat.
"""
import os
from collections import Counter, defaultdict
from typing import Dict, List, Optional

from pipeline.config_loader import load_config
from pipeline.logger import get_logger
from pipeline.storage import StorageEngine

logger = get_logger("Stage05_Analytics")


def _safe_mean(values: List[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def compute_prt_analytics(conversations: List[Dict]) -> Dict:
    """
    Change 1, 2 & 3: Group conversations by (product, region, topic/category, subtype) and
    compute trajectory-based aggregates per cell.

    Returns a dict keyed by "product|region|topic|subtype" with per-cell metrics.
    """
    total = max(len(conversations), 1)
    # region_totals for pct_of_region_traffic
    region_totals: Dict[str, int] = Counter(
        c.get("region") or c.get("nlp", {}).get("region", "unknown")
        for c in conversations
    )

    # Previous period placeholder (single run has no history; set to None)
    cells: Dict[str, Dict] = defaultdict(lambda: {
        "count": 0,
        "resolved_count": 0,
        "traj_starts": [], "traj_ends": [], "traj_deltas": [],
        "escalation_flags": [], "recovery_flags": [], "csat_proxies": [],
        "neg_sents": [], "high_sev": 0,
    })

    for c in conversations:
        nlp = c.get("nlp") or {}
        product = nlp.get("product") or c.get("product") or "unknown"
        region  = nlp.get("region")  or c.get("region")  or "unknown"
        topic   = nlp.get("category") or "other"
        subtype = nlp.get("subtype") or c.get("subtype") or "general"
        key = f"{product}|{region}|{topic}|{subtype}"

        cell = cells[key]
        cell["count"] += 1
        if c.get("has_company_response"):
            cell["resolved_count"] += 1

        traj = nlp.get("trajectory") or {}
        cell["traj_starts"].append(traj.get("start_sentiment", nlp.get("sentiment", 0.0)))
        cell["traj_ends"].append(traj.get("end_sentiment", nlp.get("sentiment", 0.0)))
        cell["traj_deltas"].append(traj.get("delta", 0.0))
        cell["escalation_flags"].append(traj.get("escalation_flag", False))
        cell["recovery_flags"].append(traj.get("recovery_flag", False))
        cell["csat_proxies"].append(traj.get("csat_proxy_score", 3.0))

        sev_label = (nlp.get("severity") or {}).get("label") if isinstance(nlp.get("severity"), dict) else nlp.get("severity", "medium")
        if sev_label in ("high", "critical"):
            cell["high_sev"] += 1

    result = {}
    for key, cell in cells.items():
        product, region, topic, subtype = key.split("|", 3)
        cnt = max(cell["count"], 1)
        reg_total = max(region_totals.get(region, 1), 1)
        esc_rate = round(sum(cell["escalation_flags"]) / cnt, 4)
        rec_rate = round(sum(cell["recovery_flags"]) / cnt, 4)
        result[key] = {
            "product": product,
            "region": region,
            "topic": topic,
            "subtype": subtype,
            "count": cell["count"],
            "pct_of_total": round(cell["count"] / total * 100, 2),
            "pct_of_region": round(cell["count"] / reg_total * 100, 2),
            "avg_start_sentiment": _safe_mean(cell["traj_starts"]),
            "avg_end_sentiment":   _safe_mean(cell["traj_ends"]),
            "avg_delta":           _safe_mean(cell["traj_deltas"]),
            "escalation_rate":     esc_rate,
            "recovery_rate":       rec_rate,
            "avg_csat_proxy":      _safe_mean(cell["csat_proxies"]),
            "resolution_rate":     round(cell["resolved_count"] / cnt, 4),
            "high_severity_rate":  round(cell["high_sev"] / cnt, 4),
        }

    return result


def compute_analytics(conversations: Optional[List[Dict]] = None, config: Optional[Dict] = None) -> Dict:
    cfg = config or load_config()
    storage = StorageEngine(cfg)
    import duckdb

    conv_file = storage.get_parquet_path("conversations.parquet", subfolder="conversations").replace("\\", "/")
    nlp_file  = storage.get_parquet_path("nlp_results.parquet",   subfolder="nlp").replace("\\", "/")

    if conversations is None and os.path.exists(conv_file) and os.path.exists(nlp_file):
        con = duckdb.connect()
        logger.info(f"Computing DuckDB analytics distributions out-of-core across {conv_file} & {nlp_file}...")

        total_convs = con.execute(f"SELECT count(*) FROM '{conv_file}'").fetchone()[0]
        total_msgs  = con.execute(f"SELECT sum(customer_turn_count + company_turn_count) FROM '{conv_file}'").fetchone()[0] or 0
        comp_resp   = con.execute(f"SELECT count(*) FROM '{conv_file}' WHERE has_company_response = true").fetchone()[0]

        cat_rows  = con.execute(f"SELECT category, count(*) as cnt FROM '{nlp_file}' GROUP BY category").fetchall()
        by_category = {r[0]: r[1] for r in cat_rows if r[0]}

        intent_rows = con.execute(f"SELECT intent, count(*) as cnt FROM '{nlp_file}' GROUP BY intent").fetchall()
        by_intent = {r[0]: r[1] for r in intent_rows if r[0]}

        sev_rows = con.execute(f"SELECT severity.label as label, count(*) as cnt FROM '{nlp_file}' GROUP BY severity.label").fetchall()
        by_severity = {r[0]: r[1] for r in sev_rows if r[0]}

        sent_rows = con.execute(f"SELECT sentiment_label, count(*) as cnt FROM '{nlp_file}' GROUP BY sentiment_label").fetchall()
        by_sentiment = {r[0]: r[1] for r in sent_rows if r[0]}

        # Change 2: trajectory aggregates from parquet (TRY_CAST guards for old files)
        try:
            traj_row = con.execute(f"""
                SELECT
                    AVG(TRY_CAST(trajectory.start_sentiment AS DOUBLE)) as avg_start,
                    AVG(TRY_CAST(trajectory.end_sentiment AS DOUBLE))   as avg_end,
                    AVG(TRY_CAST(trajectory.delta AS DOUBLE))           as avg_delta,
                    AVG(CASE WHEN TRY_CAST(trajectory.escalation_flag AS BOOLEAN) THEN 1.0 ELSE 0.0 END) as esc_rate,
                    AVG(CASE WHEN TRY_CAST(trajectory.recovery_flag AS BOOLEAN) THEN 1.0 ELSE 0.0 END)   as rec_rate,
                    AVG(TRY_CAST(trajectory.csat_proxy_score AS DOUBLE)) as avg_csat
                FROM '{nlp_file}'
            """).fetchone()
            trajectory_aggregates = {
                "avg_start_sentiment": round(traj_row[0] or 0.0, 4),
                "avg_end_sentiment":   round(traj_row[1] or 0.0, 4),
                "avg_delta":           round(traj_row[2] or 0.0, 4),
                "escalation_rate":     round(traj_row[3] or 0.0, 4),
                "recovery_rate":       round(traj_row[4] or 0.0, 4),
                "avg_csat_proxy":      round(traj_row[5] or 3.0, 4),
            }
        except Exception as e:
            logger.warning(f"Trajectory aggregates unavailable from Parquet (old schema?): {e}")
            trajectory_aggregates = {}

        # Change 1: product ├ù region ├ù topic ├ù subtype via DuckDB
        try:
            prt_rows = con.execute(f"""
                SELECT
                    COALESCE(n.product, 'unknown') as product,
                    COALESCE(n.region,  'unknown') as region,
                    n.category as topic,
                    COALESCE(n.subtype, 'general') as subtype,
                    count(*) as cnt
                FROM '{nlp_file}' n
                GROUP BY product, region, topic, subtype
            """).fetchall()
            by_prt = {}
            for r in prt_rows:
                if r[2]:
                    k = f"{r[0]}|{r[1]}|{r[2]}|{r[3]}"
                    by_prt[k] = {"product": r[0], "region": r[1], "topic": r[2], "subtype": r[3], "count": r[4]}
        except Exception as e:
            logger.warning(f"PRT grouping unavailable from Parquet (old schema?): {e}")
            by_prt = {}

        neg_count     = by_sentiment.get("negative", 0)
        high_sev_count = by_severity.get("high", 0) + by_severity.get("critical", 0)
        esc_count     = con.execute(f"SELECT count(*) FROM '{nlp_file}' WHERE len(escalation_signals) > 0").fetchone()[0]

        neg_rate     = round(neg_count / max(total_convs, 1), 4)
        high_sev_rate = round(high_sev_count / max(total_convs, 1), 4)
        esc_rate_raw  = round(esc_count / max(total_convs, 1), 4)

        avg_resp = con.execute(f"SELECT avg(first_response_time) FROM '{conv_file}' WHERE first_response_time IS NOT NULL").fetchone()[0]
        avg_resp = round(avg_resp, 2) if avg_resp else None

        unresolved_count = total_convs - comp_resp
        unresolved_rate  = round(unresolved_count / max(total_convs, 1), 4)

        daily_rows = con.execute(f"SELECT SUBSTRING(start_time, 1, 10) as day, count(*) as cnt FROM '{conv_file}' GROUP BY day ORDER BY day").fetchall()
        daily_trends = {r[0] or "2026-08-01": r[1] for r in daily_rows}
        sorted_days  = sorted(daily_trends.keys())
        counts_list  = [daily_trends[day] for day in sorted_days]

        moving_avg_3d, moving_avg_7d = {}, {}
        for i, day in enumerate(sorted_days):
            moving_avg_3d[day] = round(sum(counts_list[max(0, i - 2): i + 1]) / max(len(counts_list[max(0, i - 2): i + 1]), 1), 2)
            moving_avg_7d[day] = round(sum(counts_list[max(0, i - 6): i + 1]) / max(len(counts_list[max(0, i - 6): i + 1]), 1), 2)

        growth_pct = round(((counts_list[-1] - counts_list[-2]) / max(counts_list[-2], 1)) * 100, 2) if len(sorted_days) >= 2 else 0.0

        analytics_summary = {
            "total_conversations": total_convs,
            "total_messages": total_msgs,
            "total_complaints": total_convs,
            "by_category": by_category,
            "by_intent": by_intent,
            "by_severity": by_severity,
            "by_area": {"Global": total_convs},
            "sentiment_distribution": by_sentiment,
            "negative_sentiment_rate": neg_rate,
            "high_severity_rate": high_sev_rate,
            "escalation_rate": esc_rate_raw,
            "trajectory_aggregates": trajectory_aggregates,     # Change 2
            "by_product_region_topic_subtype": by_prt,          # Change 1
            "avg_response_time_seconds": avg_resp,
            "unresolved_count": unresolved_count,
            "unresolved_rate": unresolved_rate,
            "company_response_rate": round(comp_resp / max(total_convs, 1), 4),
            "sla_target": None,
            "sla_breach": None,
            "daily_trends": daily_trends,
            "moving_avg_3d": moving_avg_3d,
            "moving_avg_7d": moving_avg_7d,
            "growth_percentage": growth_pct,
            "area_category_breakdown": {"Global": by_category},
        }

        storage.checkpoint_mgr.save_checkpoint("stage05_analytics", analytics_summary)
        return analytics_summary

    # ΓöÇΓöÇ In-memory path (conversations list provided) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    logger.info(f"Computing in-memory analytics across {len(conversations or []):,} conversations...")
    storage = StorageEngine(cfg)

    duck_records = storage.query_parquet_duckdb(
        "conversations/conversations.parquet",
        "SELECT count(*) as total_convs, sum(customer_turn_count + company_turn_count) as total_msgs FROM {parquet_file}"
    )

    if duck_records and duck_records[0].get("total_convs"):
        total_conversations = int(duck_records[0]["total_convs"])
        total_messages      = int(duck_records[0]["total_msgs"] or 0)
    else:
        total_conversations = len(conversations)
        total_messages      = sum(c.get("customer_turn_count", 1) + c.get("company_turn_count", 0) for c in conversations)

    by_category  = Counter(c["nlp"]["category"] for c in conversations if "nlp" in c)
    by_intent    = Counter(c["nlp"]["intent"] for c in conversations if "nlp" in c)
    by_severity  = Counter(c["nlp"]["severity"]["label"] for c in conversations if "nlp" in c and isinstance(c["nlp"].get("severity"), dict))
    by_sentiment = Counter(c["nlp"]["sentiment_label"] for c in conversations if "nlp" in c)
    by_area      = Counter(c.get("area", "Global") for c in conversations)

    neg_count     = by_sentiment.get("negative", 0)
    high_sev_count = by_severity.get("high", 0) + by_severity.get("critical", 0)
    esc_count     = sum(1 for c in conversations if c.get("nlp", {}).get("escalation_signals"))

    negative_sentiment_rate = round(neg_count / max(total_conversations, 1), 4)
    high_severity_rate      = round(high_sev_count / max(total_conversations, 1), 4)
    escalation_rate         = round(esc_count / max(total_conversations, 1), 4)

    # Change 2: trajectory aggregates (in-memory)
    traj_starts, traj_ends, traj_deltas, esc_flags, rec_flags, csat_proxies = [], [], [], [], [], []
    for c in conversations:
        traj = (c.get("nlp") or {}).get("trajectory") or {}
        traj_starts.append(traj.get("start_sentiment", (c.get("nlp") or {}).get("sentiment", 0.0)))
        traj_ends.append(traj.get("end_sentiment", (c.get("nlp") or {}).get("sentiment", 0.0)))
        traj_deltas.append(traj.get("delta", 0.0))
        esc_flags.append(traj.get("escalation_flag", False))
        rec_flags.append(traj.get("recovery_flag", False))
        csat_proxies.append(traj.get("csat_proxy_score", 3.0))

    trajectory_aggregates = {
        "avg_start_sentiment": _safe_mean(traj_starts),
        "avg_end_sentiment":   _safe_mean(traj_ends),
        "avg_delta":           _safe_mean(traj_deltas),
        "escalation_rate":     round(sum(esc_flags) / max(len(esc_flags), 1), 4),
        "recovery_rate":       round(sum(rec_flags) / max(len(rec_flags), 1), 4),
        "avg_csat_proxy":      _safe_mean(csat_proxies),
    }

    # Change 1: product ├ù region ├ù topic grouping (in-memory)
    by_product_region_topic_subtype = compute_prt_analytics(conversations)

    resp_times = [c["first_response_time"] for c in conversations if c.get("first_response_time") is not None]
    avg_response_time = round(sum(resp_times) / len(resp_times), 2) if resp_times else None

    unresolved_count = sum(1 for c in conversations if not c.get("has_company_response"))
    unresolved_rate  = round(unresolved_count / max(total_conversations, 1), 4)

    daily_counts = defaultdict(int)
    for c in conversations:
        ts  = c.get("start_time") or ""
        day = ts[:10] if len(ts) >= 10 else "2026-08-01"
        daily_counts[day] += 1

    sorted_days = sorted(daily_counts.keys())
    daily_trends = {day: daily_counts[day] for day in sorted_days}
    moving_avg_3d, moving_avg_7d = {}, {}
    counts_list = [daily_counts[day] for day in sorted_days]

    for i, day in enumerate(sorted_days):
        w3 = counts_list[max(0, i - 2): i + 1]
        w7 = counts_list[max(0, i - 6): i + 1]
        moving_avg_3d[day] = round(sum(w3) / len(w3), 2)
        moving_avg_7d[day] = round(sum(w7) / len(w7), 2)

    growth_pct = round(((counts_list[-1] - counts_list[-2]) / max(counts_list[-2], 1)) * 100, 2) if len(sorted_days) >= 2 else 0.0

    analytics_summary = {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_complaints": total_conversations,
        "by_category": dict(by_category),
        "by_intent": dict(by_intent),
        "by_severity": dict(by_severity),
        "by_area": dict(by_area),
        "sentiment_distribution": dict(by_sentiment),
        "negative_sentiment_rate": negative_sentiment_rate,
        "high_severity_rate": high_severity_rate,
        "escalation_rate": escalation_rate,
        "trajectory_aggregates": trajectory_aggregates,         # Change 2
        "by_product_region_topic_subtype": by_product_region_topic_subtype,     # Change 1
        "avg_response_time_seconds": avg_response_time,
        "unresolved_count": unresolved_count,
        "unresolved_rate": unresolved_rate,
        "sla_target": None,
        "sla_breach": None,
        "daily_trends": daily_trends,
        "moving_avg_3d": moving_avg_3d,
        "moving_avg_7d": moving_avg_7d,
        "growth_percentage": growth_pct,
        "area_category_breakdown": {
            k: dict(Counter(c["nlp"]["category"] for c in conversations if c.get("area") == k and "nlp" in c))
            for k in set(by_area.keys())
        },
    }

    storage.write_parquet([analytics_summary], "analytics_summary.parquet", subfolder="analytics")
    storage.checkpoint_mgr.save_checkpoint("stage05_analytics", {"total_conversations": total_conversations})

    logger.info(
        f"[STAGE 5 ANALYTICS] Total: {total_conversations:,}, "
        f"Traj escalation_rate: {trajectory_aggregates.get('escalation_rate', 0)*100:.1f}%, "
        f"avg CSAT proxy: {trajectory_aggregates.get('avg_csat_proxy', 3.0):.2f}/5, "
        f"PRT cells: {len(by_product_region_topic_subtype)}."
    )
    return analytics_summary


if __name__ == "__main__":
    from stage01_raw_data import generate_raw_complaints
    from stage02_clean import clean_batch
    from stage03_conversations import build_conversations
    from stage04_nlp import enrich_with_nlp

    convs = enrich_with_nlp(build_conversations(clean_batch(generate_raw_complaints(50))))
    result = compute_analytics(convs)
    print("trajectory_aggregates:", result.get("trajectory_aggregates"))
    print("PRT cells:", len(result.get("by_product_region_topic", {})))
