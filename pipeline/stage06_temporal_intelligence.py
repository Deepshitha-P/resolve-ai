"""
stage06_temporal_intelligence.py ΓÇö Change 1 & 2 surgical additions:
  ΓÇó Grouping key changed from (area, category) ΓåÆ (product, region, topic).
  ΓÇó Tracks two additional time-series per PRT cell:
      avg_delta       ΓÇö average sentiment trajectory delta over time
      escalation_rate ΓÇö fraction of conversations with escalation_flag=True
  ΓÇó Trend detection added for avg_delta (worsening direction) and
    escalation_rate (rising direction).
  ΓÇó area/category fields kept in signal dict for backward compat.
"""
import statistics
from collections import defaultdict
from typing import Dict, List, Optional

from pipeline.config_loader import load_config
from pipeline.logger import get_logger

logger = get_logger("Stage06_TemporalIntelligence")


def compute_temporal_intelligence(
    conversations: Optional[List[Dict]] = None,
    config: Optional[Dict] = None,
) -> Dict:
    cfg = config or load_config()
    temp_cfg = cfg.get("temporal", {})
    spike_z   = temp_cfg.get("spike_z_threshold", 1.5)
    min_count = temp_cfg.get("min_spike_count", 3)

    logger.info(
        f"Computing temporal intelligence signals "
        f"(spike_z={spike_z}, min_count={min_count}, keyed by product├ùregion├ùtopic)..."
    )

    from pipeline.storage import StorageEngine
    import duckdb, os
    storage = StorageEngine(cfg)

    conv_file = storage.get_parquet_path("conversations.parquet", subfolder="conversations").replace("\\", "/")
    nlp_file  = storage.get_parquet_path("nlp_results.parquet",   subfolder="nlp").replace("\\", "/")

    # daily_groups[key][day] = list of conversation dicts (or just ids + trajectory snippet)
    # For in-memory path, store full traj info; for DuckDB path, store partial.
    # Structure: daily_data[(product, region, topic)][day] = {"cids": [...], "deltas": [...], "esc_flags": [...]}
    daily_data: Dict = defaultdict(lambda: defaultdict(lambda: {"cids": [], "deltas": [], "esc_flags": []}))

    if conversations is None and os.path.exists(conv_file) and os.path.exists(nlp_file):
        con = duckdb.connect()
        # Change 1: group by product, region, category (PRT)
        # TRY_CAST guards for old parquet files without trajectory columns
        try:
            rows = con.execute(f"""
                SELECT
                    COALESCE(n.product, 'unknown')  as product,
                    COALESCE(n.region,  'unknown')  as region,
                    COALESCE(n.category, 'other')   as topic,
                    COALESCE(n.subtype, 'general')  as subtype,
                    SUBSTRING(c.start_time, 1, 10)  as day,
                    list(c.conversation_id)          as cids,
                    AVG(TRY_CAST(n.trajectory.delta AS DOUBLE))           as avg_delta,
                    AVG(CASE WHEN TRY_CAST(n.trajectory.escalation_flag AS BOOLEAN) THEN 1.0 ELSE 0.0 END) as esc_rate
                FROM '{conv_file}' c
                JOIN '{nlp_file}' n ON c.conversation_id = n.conversation_id
                GROUP BY product, region, topic, subtype, day
            """).fetchall()
            for r in rows:
                k = (r[0], r[1], r[2], r[3])
                day = r[4] or "2026-08-01"
                cids = r[5] or []
                avg_d  = r[6] if r[6] is not None else 0.0
                esc_r  = r[7] if r[7] is not None else 0.0
                cell = daily_data[k][day]
                cell["cids"].extend(cids)
                cell["deltas"].append(avg_d)
                cell["esc_flags"].append(esc_r)
        except Exception as e:
            logger.warning(f"PRTS temporal DuckDB query failed: {e}.")

    else:
        for c in (conversations or []):
            nlp     = c.get("nlp") or {}
            prod    = nlp.get("product") or c.get("product") or "unknown"
            reg     = nlp.get("region")  or c.get("region")  or "unknown"
            top     = nlp.get("category") or "other"
            sub     = nlp.get("subtype") or c.get("subtype") or "general"
            k       = (prod, reg, top, sub)
            ts      = c.get("start_time") or ""
            day     = ts[:10] if len(ts) >= 10 else "2026-08-01"
            traj    = nlp.get("trajectory") or {}

            cell = daily_data[k][day]
            cell["cids"].append(c.get("conversation_id"))
            cell["deltas"].append(traj.get("delta", 0.0))
            cell["esc_flags"].append(1.0 if traj.get("escalation_flag") else 0.0)

    signals = []
    event_counter = 5000

    for prts_key, by_day in daily_data.items():
        product, region, topic, subtype = prts_key
        days_sorted = sorted(by_day.keys())
        counts = [len(by_day[d]["cids"]) for d in days_sorted]

        if len(counts) < 2:
            mean, stdev = counts[0], 0.5
        else:
            mean  = statistics.mean(counts)
            stdev = statistics.pstdev(counts) or 0.5

        latest_day   = days_sorted[-1]
        latest_count = counts[-1]
        prev_count   = counts[-2] if len(counts) >= 2 else mean

        z          = round((latest_count - mean) / max(stdev, 0.1), 2)
        change_pct = round(((latest_count - prev_count) / max(prev_count, 1)) * 100, 2)

        is_spike            = z >= spike_z and latest_count >= min_count
        is_sustained_growth = change_pct >= 50.0 and len(counts) >= 3
        is_drop             = change_pct <= -50.0

        all_deltas = [d for day in days_sorted for d in by_day[day]["deltas"]]
        avg_delta_overall = round(sum(all_deltas) / max(len(all_deltas), 1), 4)

        first_avg_d = sum(by_day[days_sorted[0]]["deltas"]) / max(len(by_day[days_sorted[0]]["deltas"]), 1)
        last_avg_d  = sum(by_day[latest_day]["deltas"]) / max(len(by_day[latest_day]["deltas"]), 1)
        delta_direction = "worsening" if last_avg_d < first_avg_d - 0.05 else ("improving" if last_avg_d > first_avg_d + 0.05 else "stable")

        all_esc = [e for day in days_sorted for e in by_day[day]["esc_flags"]]
        overall_esc_rate = round(sum(all_esc) / max(len(all_esc), 1), 4)

        first_avg_esc = sum(by_day[days_sorted[0]]["esc_flags"]) / max(len(by_day[days_sorted[0]]["esc_flags"]), 1)
        last_avg_esc  = sum(by_day[latest_day]["esc_flags"]) / max(len(by_day[latest_day]["esc_flags"]), 1)
        esc_direction = "rising" if last_avg_esc > first_avg_esc + 0.05 else ("falling" if last_avg_esc < first_avg_esc - 0.05 else "stable")

        trend = "spiking" if is_spike else ("sustained_growth" if is_sustained_growth else ("sudden_drop" if is_drop else ("increasing" if z > 0 else "stable")))

        event_counter += 1
        supporting_cases = by_day[latest_day]["cids"][:10]

        signals.append({
            "event_id":            f"TEMP-EVT-{event_counter}",
            "product":             product,
            "region":              region,
            "topic":               topic,
            "subtype":             subtype,
            "area":                region,
            "category":            topic,
            "metric":              "complaint_volume",
            "latest_day":          latest_day,
            "latest_day_count":    latest_count,
            "current_value":       latest_count,
            "previous_value":      prev_count,
            "change_percentage":   change_pct,
            "historical_avg":      round(mean, 2),
            "z_score":             z,
            "is_spike":            is_spike,
            "trend":               trend,
            "severity":            "high" if is_spike else "medium",
            "supporting_case_ids": supporting_cases,
            "daily_counts":        {d: len(by_day[d]["cids"]) for d in days_sorted},
            # Change 2: trajectory trends
            "avg_delta_overall":   avg_delta_overall,
            "delta_direction":     delta_direction,
            "avg_delta_first_day": round(first_avg_d, 4),
            "avg_delta_last_day":  round(last_avg_d, 4),
            "escalation_rate":     overall_esc_rate,
            "esc_rate_direction":  esc_direction,
            "esc_rate_first_day":  round(first_avg_esc, 4),
            "esc_rate_last_day":   round(last_avg_esc, 4),
        })

    signals.sort(key=lambda s: s["z_score"], reverse=True)
    active_spikes = [s for s in signals if s["is_spike"]]

    logger.info(
        f"[STAGE 6 TEMPORAL INTELLIGENCE] Detected {len(signals):,} temporal signals "
        f"({len(active_spikes):,} active spikes) keyed by (product├ùregion├ùtopic)."
    )
    return {
        "signals": signals,
        "active_spikes": active_spikes,
    }


if __name__ == "__main__":
    from stage01_raw_data import generate_raw_complaints
    from stage02_clean import clean_batch
    from stage03_conversations import build_conversations
    from stage04_nlp import enrich_with_nlp

    convs = enrich_with_nlp(build_conversations(clean_batch(generate_raw_complaints(50))))
    result = compute_temporal_intelligence(convs)
    for s in result["signals"][:3]:
        print(s["product"], s["region"], s["topic"], "|", s["trend"],
              "| esc_rate:", s["escalation_rate"], "| delta_dir:", s["delta_direction"])
