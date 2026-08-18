"""
stage08_analytics_snapshots.py ΓÇö Change 1 & 2 surgical additions:
  ΓÇó build_prt_snapshots(): generates one snapshot document per (product, region, topic)
    cell using the exact template from the spec.
  ΓÇó Global snapshot now includes trajectory_aggregates.
  ΓÇó Spike snapshots include delta_direction and esc_rate_direction.
  ΓÇó Incident snapshots include product, region, escalation_rate.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pipeline.config_loader import load_config
from pipeline.logger import get_logger
from pipeline.schemas import AnalyticsSnapshot

logger = get_logger("Stage08_AnalyticsSnapshots")


def _diag_sentence(product: str, region: str, topic: str, escalation_rate: float, count: int) -> str:
    """
    Generate a one-line diagnostic distinguishing volume-driven vs. support-handling issues.
    Escalation rate > 25% ΓåÆ support handling problem; otherwise ΓåÆ underlying issue.
    """
    esc_pct = round(escalation_rate * 100, 1)
    if escalation_rate > 0.25:
        return (
            f"Root cause likely poor support handling: {esc_pct}% of {product} complaints in {region} "
            f"escalated mid-thread despite agent contact, suggesting resolution quality issue rather than "
            f"pure volume surge."
        )
    else:
        return (
            f"Root cause likely underlying {topic} issue: escalation rate is only {esc_pct}%, "
            f"suggesting the {product} problem in {region} is self-contained and not compounded by "
            f"support failure."
        )



# ΓöÇΓöÇ Fix A: Minimum volume threshold for individual PRT snapshots ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
# Cells below this volume are too thin to be useful standalone evidence docs.
# They are rolled up into topic-level aggregate snapshots instead.
MIN_SNAPSHOT_VOLUME = 3


def build_prt_snapshots(
    prt_analytics: Dict,
    prt_temporal: Optional[Dict] = None,
    prt_clusters: Optional[Dict] = None,
) -> List[Dict]:
    """
    Fix A: Generate one snapshot per (product, region, topic) cell ONLY when
    complaint count >= MIN_SNAPSHOT_VOLUME.  Thin cells (count < threshold) are
    merged by topic into a single rolled-up SNAP-TOPIC-{topic} aggregate so
    billing/network/etc. queries always find one representative document instead
    of dozens of near-empty slivers.
    """
    now = datetime.now(timezone.utc).isoformat()
    snapshots = []

    # Build a lookup: prt_key ΓåÆ temporal signal for trend info
    temporal_lookup: Dict[str, Dict] = {}
    if prt_temporal:
        for sig in prt_temporal.get("signals", []):
            k = f"{sig.get('product', 'unknown')}|{sig.get('region', 'unknown')}|{sig.get('topic', 'other')}|{sig.get('subtype', 'general')}"
            temporal_lookup[k] = sig

    # Build a lookup: prt_key ΓåÆ pain_score from clusters
    cluster_lookup: Dict[str, float] = {}
    if prt_clusters:
        for _, cl in (prt_clusters.get("clusters") or {}).items():
            k = f"{cl.get('product', 'unknown')}|{cl.get('region', 'unknown')}|{cl.get('topic', 'other')}|{cl.get('subtype', 'general')}"
            cluster_lookup[k] = cl.get("pain_point_impact", {}).get("pain_score", 50.0)

    # ΓöÇΓöÇ Pass 1: separate full-volume cells from thin cells ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # topic_rollup accumulates metrics for thin cells keyed by topic only
    topic_rollup: Dict[str, Dict] = {}  # topic ΓåÆ accumulated metrics dict

    for prt_key, cell in prt_analytics.items():
        product = cell.get("product", "unknown")
        region  = cell.get("region",  "unknown")
        topic   = cell.get("topic",   "other")
        subtype = cell.get("subtype", "general")
        count   = cell.get("count", 0)

        # Skip topic="other"
        if topic == "other" or count == 0:
            continue
        
        pct_of_total  = cell.get("pct_of_total", 0.0)
        pct_of_region = cell.get("pct_of_region", 0.0)

        avg_start = cell.get("avg_start_sentiment", 0.0)
        avg_end   = cell.get("avg_end_sentiment",   0.0)
        avg_delta = cell.get("avg_delta", 0.0)
        esc_rate  = cell.get("escalation_rate", 0.0)
        rec_rate  = cell.get("recovery_rate", 0.0)
        avg_csat  = cell.get("avg_csat_proxy", 3.0)
        res_rate  = cell.get("resolution_rate", 0.0)

        sig = temporal_lookup.get(prt_key, {})
        trend_dir    = sig.get("trend", "stable")
        trend_periods = 1

        pain_score = cluster_lookup.get(prt_key, round(esc_rate * 50 + (1 - res_rate) * 30, 1))
        insight_text = _diag_sentence(product, region, topic, esc_rate, count)

        # ΓöÇΓöÇ Fix A gate: skip thin cells as standalone docs; accumulate for rollup ΓöÇΓöÇ
        if count < MIN_SNAPSHOT_VOLUME:
            rb = topic_rollup.setdefault(topic, {
                "total_count": 0, "esc_sum": 0.0, "rec_sum": 0.0,
                "csat_sum": 0.0, "res_sum": 0.0, "start_sum": 0.0,
                "end_sum": 0.0, "pain_scores": [], "products": set(),
                "regions": set(), "trend": "stable", "cells": 0,
            })
            rb["total_count"] += count
            rb["esc_sum"]     += esc_rate * count
            rb["rec_sum"]     += rec_rate * count
            rb["csat_sum"]    += avg_csat * count
            rb["res_sum"]     += res_rate * count
            rb["start_sum"]   += avg_start * count
            rb["end_sum"]     += avg_end * count
            rb["pain_scores"].append(pain_score)
            rb["products"].add(product)
            rb["regions"].add(region)
            rb["cells"] += 1
            # Use the most-alarming trend direction
            if trend_dir in ("rising", "spike"):
                rb["trend"] = trend_dir
            continue  # do NOT emit this thin cell as a standalone snapshot

        # ΓöÇΓöÇ Full-volume cell: emit as normal PRT snapshot ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
        esc_pct = round(esc_rate * 100, 1)
        res_pct = round(res_rate * 100, 1)
        sent = f"{avg_start:.2f}->{avg_end:.2f} (delta: {avg_delta:+.2f})"
        trend_str = f"{trend_dir} for {trend_periods} period(s)"
        csat = round(avg_csat, 2)

        doc_text = (
            f'Document: "{product} - {region} - {topic} ({subtype}) - current"\n'
            f'Period: current\n'
            f'Topic: {topic}\n'
            f'Product: {product}\n'
            f'Region: {region}\n'
            f'Subtype: {subtype}\n'
            f'Volume: {count} complaints\n'
            f'CSAT Proxy: {csat} / 5\n'
            f'Escalation Rate: {esc_pct}%\n'
            f'Resolution Rate: {res_pct}%\n'
            f'Sentiment: {sent}\n'
            f'Trend: {trend_str}\n'
            f'Pain Score: {pain_score}\n\n'
            f'Summary:\n{insight_text}'
        )

        snap_id = f"SNAP-PRT-{product}-{region}-{topic}-{subtype}".replace(" ", "_").upper()
        snap = AnalyticsSnapshot(
            document_id=snap_id,
            document_type="prt_analytics_snapshot",
            source_type="operational_analytics",
            period="current",
            topic=topic,
            region=region,
            product=product,
            created_at=now,
            text=doc_text,
            metrics={
                **cell,
                "pain_score": pain_score,
                "trend": trend_dir,
                "insight": insight_text,
            },
        )
        snapshots.append(snap.model_dump())

    # ΓöÇΓöÇ Pass 2: emit one rolled-up SNAP-TOPIC-{topic} per thin-cell group ΓöÇΓöÇΓöÇ
    # Only emitted when the accumulated topic volume is >= 1 (always true if any thin cells exist).
    # Groups multiple products/regions together: e.g. all "billing" slivers
    # become one SNAP-TOPIC-BILLING with correct aggregate volume.
    for topic, rb in topic_rollup.items():
        total = max(rb["total_count"], 1)
        avg_esc   = round(rb["esc_sum"]   / total, 4)
        avg_rec   = round(rb["rec_sum"]   / total, 4)
        avg_csat  = round(rb["csat_sum"]  / total, 3)
        avg_res   = round(rb["res_sum"]   / total, 4)
        avg_start = round(rb["start_sum"] / total, 3)
        avg_end   = round(rb["end_sum"]   / total, 3)
        avg_delta = round(avg_end - avg_start, 3)
        max_pain  = round(max(rb["pain_scores"]) if rb["pain_scores"] else 0.0, 1)
        products_str = ", ".join(sorted(rb["products"]))
        regions_str  = ", ".join(sorted(rb["regions"]))
        trend_dir    = rb["trend"]
        n_cells      = rb["cells"]

        insight_text = _diag_sentence("multiple products", regions_str, topic, avg_esc, total)

        doc_text = (
            f'Document: "TOPIC-ROLLUP - {topic} - current"\n'
            f"---\n"
            f"Aggregated from {n_cells} thin product├ùregion cells (each < {MIN_SNAPSHOT_VOLUME} complaints).\n"
            f"Products covered: {products_str} | Regions covered: {regions_str}\n"
            f"Volume: {total} complaints (combined across all cells)\n"
            f"Sentiment trajectory: starts at {avg_start:.3f}, ends at {avg_end:.3f} (delta: {avg_delta:+.3f})\n"
            f"Escalation rate: {round(avg_esc * 100, 1)}% of conversations worsened mid-thread\n"
            f"Recovery rate: {round(avg_rec * 100, 1)}% recovered after a negative dip\n"
            f"CSAT proxy: {avg_csat:.2f}/5 (aggregated baseline)\n"
            f"Resolution rate: {round(avg_res * 100, 1)}%\n"
            f"Pain score: {max_pain}/100 (peak across cells)\n"
            f"Trend: {trend_dir}\n"
            f"Insight: {insight_text}"
        )

        snap_id = f"SNAP-TOPIC-{topic}".replace(" ", "_").upper()
        snap = AnalyticsSnapshot(
            document_id=snap_id,
            document_type="topic_rollup_snapshot",
            source_type="operational_analytics",
            period="current",
            topic=topic,
            region="multi-region",
            product="multi-product",
            created_at=now,
            text=doc_text,
            metrics={
                "count": total,
                "volume": total,
                "pain_score": max_pain,
                "escalation_rate": avg_esc,
                "recovery_rate": avg_rec,
                "avg_csat_proxy": avg_csat,
                "resolution_rate": avg_res,
                "avg_start_sentiment": avg_start,
                "avg_end_sentiment": avg_end,
                "avg_delta": avg_delta,
                "trend": trend_dir,
                "insight": insight_text,
                "n_source_cells": n_cells,
                "products_covered": list(rb["products"]),
                "regions_covered": list(rb["regions"]),
            },
        )
        snapshots.append(snap.model_dump())

    logger.info(
        f"[STAGE 8] PRT snapshots: {sum(1 for s in snapshots if s.get('document_type') == 'prt_analytics_snapshot')} full-volume, "
        f"{len(topic_rollup)} topic rollups (from thin cells). "
        f"Suppressed {sum(rb['cells'] for rb in topic_rollup.values())} sub-threshold slivers."
    )
    return snapshots



def build_snapshots(
    analytics: Dict,
    temporal: Dict,
    clusters: Dict,
    config: Optional[Dict] = None,
) -> List[Dict]:
    cfg = config or load_config()
    now = datetime.now(timezone.utc).isoformat()
    snapshots: List[Dict] = []

    # 1. Global Analytics Snapshot (Change 2: include trajectory aggregates)
    traj_agg = analytics.get("trajectory_aggregates") or {}
    traj_summary = ""
    if traj_agg:
        traj_summary = (
            f" Sentiment trajectory: avg_start={traj_agg.get('avg_start_sentiment', 0):.3f}, "
            f"avg_end={traj_agg.get('avg_end_sentiment', 0):.3f}, "
            f"avg_delta={traj_agg.get('avg_delta', 0):+.3f}. "
            f"Trajectory escalation_rate: {traj_agg.get('escalation_rate', 0)*100:.1f}%. "
            f"Recovery rate: {traj_agg.get('recovery_rate', 0)*100:.1f}%. "
            f"Avg CSAT proxy: {traj_agg.get('avg_csat_proxy', 3.0):.2f}/5."
        )

    global_text = (
        f"Global operational analytics snapshot: {analytics['total_conversations']} total conversations analyzed. "
        f"Top categories: {analytics['by_category']}. "
        f"Severity distribution: {analytics['by_severity']}. "
        f"Negative sentiment rate: {analytics['negative_sentiment_rate']*100:.1f}%. "
        f"Escalation rate (signal-based): {analytics['escalation_rate']*100:.1f}%."
        f"{traj_summary}"
    )
    global_snap = AnalyticsSnapshot(
        document_id="SNAP-GLOBAL",
        document_type="global_analytics_snapshot",
        source_type="operational_analytics",
        period="global",
        topic="all",
        region="global",
        product="all",
        created_at=now,
        text=global_text,
        metrics=analytics,
    )
    snapshots.append(global_snap.model_dump())

    # 2. PRT Snapshots (Change 1 & 2) ΓÇö primary new output
    prt_data = analytics.get("by_product_region_topic_subtype")
    if prt_data:
        prt_snaps = build_prt_snapshots(prt_data, prt_temporal=temporal, prt_clusters=clusters)
        snapshots.extend(prt_snaps)
        logger.info(f"[STAGE 8] Generated {len(prt_snaps)} PRT snapshot documents.")

    # 3. Temporal Spike Snapshots (Change 2: include delta/esc trend)
    for s in temporal.get("active_spikes", []):
        product  = s.get("product", s.get("area", "unknown"))
        region   = s.get("region",  s.get("area", "unknown"))
        topic    = s.get("topic",   s.get("category", "other"))
        snap_id  = f"SNAP-SPIKE-{product}-{region}-{topic}".replace(" ", "_").upper()
        delta_dir = s.get("delta_direction", "unknown")
        esc_dir   = s.get("esc_rate_direction", "unknown")
        esc_rate  = s.get("escalation_rate", 0.0)
        spike_text = (
            f"Temporal spike detected: {topic} complaints for product '{product}' in region '{region}' "
            f"reached {s['latest_day_count']} on {s['latest_day']}, vs historical average of "
            f"{s['historical_avg']} (z-score {s['z_score']}). Trend: {s['trend']}. "
            f"Sentiment trajectory direction: {delta_dir}. "
            f"Escalation rate: {round(esc_rate*100,1)}% ({esc_dir})."
        )
        spike_snap = AnalyticsSnapshot(
            document_id=snap_id,
            document_type="temporal_spike_snapshot",
            source_type="operational_analytics",
            period="daily",
            topic=topic,
            region=region,
            product=product,
            created_at=now,
            text=spike_text,
            metrics=s,
        )
        snapshots.append(spike_snap.model_dump())

    # 4. Incident Cluster Snapshots (Change 1 & 2: include product, region, escalation_rate)
    for inc in clusters.get("incident_candidates", []):
        inc_id   = inc["incident_id"]
        product  = inc.get("product", "unknown")
        region   = inc.get("region", inc.get("area", "unknown"))
        topic    = inc.get("topic", inc.get("category", "other"))
        esc_rate = inc.get("escalation_rate", 0.0)
        inc_text = (
            f"Potential incident cluster {inc_id}: {inc['affected_complaint_count']} "
            f"complaints about '{topic}' for product '{product}' in region '{region}'. "
            f"Escalation rate: {round(esc_rate*100,1)}% "
            f"({'support-handling concern' if esc_rate > 0.25 else 'issue-driven'}). "
            f"Pain Score: {inc.get('pain_score', 75.0)}/100. Keywords: {', '.join(inc['keywords'])}."
        )
        inc_snap = AnalyticsSnapshot(
            document_id=inc_id,
            document_type="incident_snapshot",
            source_type="operational_analytics",
            period="cluster_period",
            topic=topic,
            region=region,
            product=product,
            created_at=now,
            text=inc_text,
            metrics=inc,
        )
        snapshots.append(inc_snap.model_dump())

    logger.info(f"[STAGE 8 ANALYTICS SNAPSHOTS] Created {len(snapshots)} retrievable snapshot documents.")
    return snapshots


if __name__ == "__main__":
    from stage01_raw_data import generate_raw_complaints
    from stage02_clean import clean_batch
    from stage03_conversations import build_conversations
    from stage04_nlp import enrich_with_nlp
    from stage05_analytics import compute_analytics
    from stage06_temporal_intelligence import compute_temporal_intelligence
    from stage07_issue_clusters import cluster_issues

    convs  = enrich_with_nlp(build_conversations(clean_batch(generate_raw_complaints(50))))
    snaps  = build_snapshots(
        compute_analytics(convs),
        compute_temporal_intelligence(convs),
        cluster_issues(convs),
    )
    for s in snaps:
        print(s["document_id"], "->", s["text"][:120])
