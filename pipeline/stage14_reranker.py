import math
from typing import Any, Dict, List

# Source trust & layer priority weights for candidate reranking
LAYER_PRIORITY_WEIGHTS = {
    "runbooks": 1.25,                   # Authoritative technical SOPs
    "policies": 1.20,                   # Authoritative SLA & business rules
    "resolved_historical_cases": 1.15,  # High-trust proven resolution precedents
    "issue_clusters": 1.10,             # Aggregated incident clusters & pain scores
    "temporal_events": 1.05,            # Volume surge signals
    "conversations": 0.95,              # Multi-turn thread history
    "customer_cases": 0.90,             # Granular raw customer complaints
    "analytics_snapshots": 0.85,        # Operational KPI metrics (PRT + rollups)
    "topic_rollup_snapshot": 0.88,      # Fix A rollup docs ΓÇö slightly above raw PRT
    "historical_insights": 0.80,        # Past LLM post-mortems
}


def rerank(results: List[Dict], query_type: str = "customer_complaint") -> List[Dict]:
    """
    Stage 14: Layer-Priority, Source-Trust & Volume-Weighted Candidate Reranker.

    Fix B: adds a log-scaled volume_boost multiplier to the rerank score so
    high-mention-count snapshots outrank 1-complaint slivers when semantic
    similarity is comparable.

    Formula:
        rerank_score = combined_score ├ù layer_priority ├ù volume_boost

    volume_boost = 1.0 + 0.1 ├ù min(log10(max(volume, 1)), 3.0)
        ΓåÆ vol=1   ΓåÆ boost = 1.00  (no boost)
        ΓåÆ vol=10  ΓåÆ boost = 1.10
        ΓåÆ vol=100 ΓåÆ boost = 1.20
        ΓåÆ vol=330 ΓåÆ boost = 1.25  (capped at ~1.25 for reasonable volumes)

    Runbooks / policies / issue_clusters carry no volume metadata and default
    to vol=1 (boost=1.0), so they are not penalised ΓÇö their layer_priority
    weight already makes them authoritative.
    """
    reranked = []
    for r in results:
        doc = r.get("doc", {})
        layer = r.get("layer") or doc.get("type") or doc.get("document_type", "unknown")
        priority = LAYER_PRIORITY_WEIGHTS.get(layer, 1.0)

        comb_score = r.get("combined_score", r.get("vector_score", 0.5))

        # ┌── Fix B: volume boost ──────────────────────────────────────────
        metrics = doc.get("metrics", {}) if doc else {}
        meta = doc.get("metadata", {}) if doc else {}
        vol = int(
            metrics.get("count")
            or metrics.get("volume")
            or metrics.get("complaint_count")
            or metrics.get("total_complaints")
            or meta.get("volume")
            or 1   # default: no boost (covers runbooks, policies, etc.)
        )
        # Log10 scale, capped at 3 decades (1000 complaints → max boost)
        volume_boost = round(1.0 + 0.1 * min(math.log10(max(vol, 1)), 3.0), 4)

        # ┌── Fix C: Pain Score boost for operational priority queries ──────
        pain_boost = 1.0
        # Operational queries: incident, temporal_spike, kpi_metric, etc.
        operational_queries = ["incident", "temporal_spike", "kpi_metric"]
        if query_type in operational_queries and layer == "issue_clusters":
            pain_score = float(meta.get("pain_score", 0.0))
            pain_boost = round(1.0 + (pain_score / 100.0) * 0.3, 4)

        rerank_score = round(comb_score * priority * volume_boost * pain_boost, 4)

        r_copy = dict(r)
        r_copy["layer"]         = layer
        r_copy["rerank_score"]  = rerank_score
        r_copy["volume_boost"]  = volume_boost   # expose for debugging / evidence metadata
        reranked.append(r_copy)

    # Sort candidates by rerank_score descending
    return sorted(reranked, key=lambda item: item["rerank_score"], reverse=True)

