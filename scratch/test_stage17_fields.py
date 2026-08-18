"""
Quick smoke-test for stage17 recommended_actions and priority.
Runs stage17 directly (no full pipeline) with synthetic signals.
"""
import sys, os
sys.path.insert(0, os.getcwd())

from pipeline.stage17_llm_grounded_insight import generate_policy_grounded_insight

# --- Query 1: account complaints (customer_complaint, medium confidence, negative sentiment)
nlp1 = {
    "intent": "account_issue",
    "severity": "medium",
    "sentiment_label": "negative",
    "trajectory": {"escalation_flag": False, "delta": -0.08, "start_sentiment": -0.1, "end_sentiment": -0.18, "csat_proxy_score": 2.8},
    "escalation_rate": 0.08,
}
ev1 = [{"doc_id": "DOC-CLUSTER-7", "layer": "issue_clusters", "relevance_score": 0.72, "trust_score": 0.82, "excerpt": "Account login failures spiked 34% over 7 days."}]
r1 = generate_policy_grounded_insight(
    query="why are account complaints increasing?",
    nlp_signal=nlp1,
    evidence_chain=ev1,
    confidence=0.72,
    query_type="customer_complaint",
)
print("=== Query 1: account complaints ===")
print(f"  priority:            {r1['priority']!r}")
print(f"  recommended_actions: {r1['recommended_actions']}")
print()

# --- Query 2: policy query (low confidence, neutral)
nlp2 = {
    "intent": "refund_policy",
    "severity": "low",
    "sentiment_label": "neutral",
    "trajectory": {"escalation_flag": False, "delta": 0.0},
    "escalation_rate": 0.02,
}
ev2 = [{"doc_id": "POL-REFUND-01", "layer": "policies", "relevance_score": 0.55, "trust_score": 0.75, "excerpt": "Refund processed within 7-14 business days per service tier."}]
r2 = generate_policy_grounded_insight(
    query="what is the refund policy for service delays?",
    nlp_signal=nlp2,
    evidence_chain=ev2,
    confidence=0.45,
    query_type="policy",
)
print("=== Query 2: refund policy (low confidence) ===")
print(f"  priority:            {r2['priority']!r}")
print(f"  recommended_actions: {r2['recommended_actions']}")
print()

# --- Query 3: incident/temporal spike (escalation flag + high confidence)
nlp3 = {
    "intent": "service_outage",
    "severity": "critical",
    "sentiment_label": "negative",
    "trajectory": {"escalation_flag": True, "delta": -0.35, "csat_proxy_score": 1.5},
    "escalation_rate": 0.32,
}
ev3 = [{"doc_id": "SNAP-GLOBAL", "layer": "analytics_snapshots", "relevance_score": 0.90, "trust_score": 0.95, "excerpt": "Service outage escalation rate 32% — highest in 90 days."}]
r3 = generate_policy_grounded_insight(
    query="why is broadband down in London?",
    nlp_signal=nlp3,
    evidence_chain=ev3,
    confidence=0.90,
    query_type="incident",
)
print("=== Query 3: broadband outage incident (escalation + critical) ===")
print(f"  priority:            {r3['priority']!r}")
print(f"  recommended_actions: {r3['recommended_actions']}")
