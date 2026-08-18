import re as _re
from typing import Any, Dict, List, Optional


# ΓöÇΓöÇ Fix C: Minimum signal floor for evidence admission ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
MIN_EVIDENCE_VOLUME = 3
LOW_VOLUME_THRESHOLD = 5


def _doc_volume(r: Dict) -> int:
    """
    Extract complaint volume from a reranked result.

    Priority order:
    1. doc.metrics dict (populated in-memory during batch pipeline)
    2. doc text field ΓÇö regex parse "Volume: N complaints" (survives ChromaDB serialisation)
    3. 999 sentinel ΓÇö means no volume metadata ΓåÆ always admitted (runbooks, policies, etc.)
    """
    doc = r.get("doc", {}) or {}

    # 1. Try metrics dict (works in-memory / parquet, may be empty from ChromaDB)
    metrics = doc.get("metrics") or {}
    if isinstance(metrics, dict):
        vol = (
            metrics.get("count")
            or metrics.get("volume")
            or metrics.get("complaint_count")
            or metrics.get("total_complaints")
        )
        if vol is not None:
            return int(vol)

    # 2. Parse from text content ΓÇö "Volume: 34 complaints" pattern written by Stage 8
    text = r.get("text") or doc.get("text") or doc.get("content") or ""
    m = _re.search(r"Volume:\s*(\d+)\s*complaints", text, _re.IGNORECASE)
    if m:
        return int(m.group(1))

    # 3. No volume info ΓÇö sentinel value ΓåÆ always admitted
    return 999



def build_evidence_and_confidence(reranked_results: List[Dict], nlp_signal: Optional[Dict] = None, top_n: int = 3) -> Dict[str, Any]:
    """
    Stage 15: Evidence Assembly & Multi-Factor Confidence Scoring.
    Assembles evidence items citing doc_id, layer, title, excerpt, and rerank_score.
    Computes evidence-driven confidence score (never fabricates evidence).

    Fix C: Excludes low-volume candidates (count < MIN_EVIDENCE_VOLUME) before
    assembling the chain. Applies a low_volume_penalty when all accepted evidence
    is thin (count < LOW_VOLUME_THRESHOLD), so the LLM receives a confidence
    signal that reflects data quality, not just semantic similarity.
    """
    nlp = nlp_signal or {}

    # ΓöÇΓöÇ Fix C: soft-filter low-volume candidates ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # Only filter analytics_snapshots / topic_rollup docs; never filter
    # runbooks / policies / issue_clusters (they have no volume metadata ΓåÆ 999).
    filtered = [r for r in reranked_results if _doc_volume(r) >= MIN_EVIDENCE_VOLUME]
    if not filtered:
        # Fall back ΓÇö data genuinely thin; use unfiltered but flag it
        filtered = reranked_results
        thin_fallback = True
    else:
        thin_fallback = False

    top = filtered[:top_n]

    if not top:
        return {
            "evidence_chain": [],
            "confidence_score": 0.0,
            "confidence_breakdown": {
                "avg_relevance": 0.0,
                "source_diversity": 0.0,
                "has_authoritative_evidence": False,
                "has_resolution_precedent": False,
                "severity_alignment": 0.0,
            },
            "status": "insufficient_evidence"
        }

    evidence_chain = []
    for r in top:
        doc = r.get("doc", {})
        doc_id = r.get("doc_id") or doc.get("doc_id") or doc.get("document_id") or "UNKNOWN"
        layer = r.get("layer") or doc.get("type") or doc.get("document_type", "unknown")
        title = r.get("title") or doc.get("title", "")
        text = r.get("text") or doc.get("text") or doc.get("content", "")
        vol = _doc_volume(r)

        evidence_chain.append({
            "source_id": doc_id,
            "doc_id": doc_id,
            "layer": layer,
            "source_type": layer,
            "title": title,
            "excerpt": text[:250],
            "text": text,
            "relevance_score": r.get("rerank_score", 0.0),
            "complaint_volume": vol if vol != 999 else None,   # expose volume to LLM prompt
            "metadata": r.get("metadata") or doc.get("metadata", {}),
        })

    # Multi-factor evidence quality evaluation
    avg_relevance = round(sum(e["relevance_score"] for e in evidence_chain) / len(evidence_chain), 3)
    layers_present = {e["layer"] for e in evidence_chain}
    source_diversity = round(min(len(layers_present) / 3.0, 1.0), 3)

    has_authoritative_evidence = any(l in ("runbooks", "policies") for l in layers_present)
    has_resolution_precedent = "resolved_historical_cases" in layers_present

    sev = nlp.get("severity")
    if isinstance(sev, dict):
        sev_label = sev.get("label", "low")
    else:
        sev_label = str(sev or "low")

    severity_alignment = 1.0 if sev_label in ("high", "critical") and (has_authoritative_evidence or has_resolution_precedent) else 0.6

    weights = {
        "avg_relevance": 0.40,
        "source_diversity": 0.15,
        "authoritative_evidence": 0.25,
        "severity_alignment": 0.20,
    }

    confidence = (
        weights["avg_relevance"] * min(avg_relevance, 1.0)
        + weights["source_diversity"] * source_diversity
        + weights["authoritative_evidence"] * (1.0 if (has_authoritative_evidence or has_resolution_precedent) else 0.4)
        + weights["severity_alignment"] * severity_alignment
    )

    # Existing floor: max relevance < 0.20
    max_relevance = max(e["relevance_score"] for e in evidence_chain) if evidence_chain else 0.0
    if max_relevance < 0.20:
        confidence = 0.15

    # ΓöÇΓöÇ Fix C: low-volume confidence penalty ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # If we're in thin-fallback mode OR all admitted evidence has very low volume,
    # penalise confidence so the LLM knows to hedge its answer.
    volumes = [e["complaint_volume"] for e in evidence_chain if e["complaint_volume"] is not None]
    all_thin = volumes and all(v < LOW_VOLUME_THRESHOLD for v in volumes)
    low_volume_penalty = 0.0
    if thin_fallback or all_thin:
        low_volume_penalty = 0.15
        confidence = max(confidence - low_volume_penalty, 0.10)

    confidence = round(min(confidence, 0.95), 2)

    return {
        "evidence_chain": evidence_chain,
        "confidence_score": confidence,
        "confidence_breakdown": {
            "avg_relevance": avg_relevance,
            "source_diversity": source_diversity,
            "has_authoritative_evidence": has_authoritative_evidence,
            "has_resolution_precedent": has_resolution_precedent,
            "severity_alignment": severity_alignment,
            "low_volume_penalty": low_volume_penalty,
            "thin_evidence_fallback": thin_fallback,
        },
        "status": "sufficient_evidence" if max_relevance >= 0.20 else "insufficient_evidence"
    }

