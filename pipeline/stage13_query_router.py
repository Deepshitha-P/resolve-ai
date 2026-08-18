import os
import re
from typing import Any, Dict, List, Optional
from pipeline.stage02_clean import clean_text



ROUTER_INTENT_MAP = {
    # 0. Raw Data Deep Dive (Retrieval Loop) - Highest Priority
    "deep_dive_raw_data": {
        "keywords": ["raw data", "raw tweets", "specific customer", "find me cases where", "deep dive", "search raw", "unfiltered"],
        "layers": ["raw_data_warehouse"], 
        "reason": "Query requests highly specific, granular raw data not captured in pre-computed summaries."
    },
    # 1. Incident Clusters (Moved up to prevent 'resolved today' being caught by historical_precedent 'resolved')
    "incident": {
        "keywords": ["cluster", "incident", "pattern", "widespread", "pain point", "major issue", "outage cluster", "risk", "highest risk", "problems", "highest priority problem", "urgent issue", "critical issue", "biggest customer issue", "emerging problem", "to be resolved today", "needs to be resolved"],
        "layers": ["issue_clusters"],
        "reason": "Query requests macro incident cluster analysis or pain point scores."
    },
    # 2. Historical Precedent / Resolution Queries
    "historical_precedent": {
        "keywords": ["resolution", "resolved", "precedent", "how was it fixed", "fix pattern", "refunded", "solution precedent"],
        "layers": ["resolved_historical_cases"],
        "reason": "Query requests past resolution precedent or proven fix patterns."
    },
    # 3. Operational Procedures / Runbooks
    "operational_procedure": {
        "keywords": ["runbook", "sop", "procedure", "troubleshoot", "node outage", "restart", "fiber splice", "technical step"],
        "layers": ["runbooks", "issue_clusters", "analytics_snapshots"],
        "reason": "Query requests technical standard operating procedures or runbook steps."
    },
    # 4. Network / Outage — specific route so 'down' doesn't fall into customer_complaint
    "network_outage": {
        "keywords": ["broadband", "internet down", "no service", "outage", "service down", "signal", "network", "wifi down", "fibre"],
        "layers": ["issue_clusters", "analytics_snapshots", "runbooks", "customer_cases"],
        "reason": "Query relates to a network or service outage — pulling issue clusters, snapshots, and runbooks."
    },
    # 5. Policies & Rules
    "policy": {
        "keywords": ["policy", "sla", "refund policy", "rule", "terms", "auto-refund", "escalation rule", "allowance"],
        "layers": ["policies"],
        "reason": "Query requests operational SLA, refund, or business policies."
    },
    # 5. Temporal Spikes & Trends
    "temporal_spike": {
        "keywords": ["spike", "surge", "trend", "volume surge", "z-score", "increase", "spike on"],
        "layers": ["temporal_events"],
        "reason": "Query requests temporal volume surge signals or spike trends."
    },
    # 6. Operational KPIs & Snapshots
    "kpi_metric": {
        "keywords": ["kpi", "metric", "snapshot", "summary", "total conversations", "negative sentiment rate", "sla breach", "categories", "breakdown", "distribution", "sentiment", "overall", "report", "analytics"],
        "layers": ["analytics_snapshots"],
        "reason": "Query requests executive KPI metrics or operational snapshot summaries."
    },
    # 7. Previous Generated Insights
    "previous_insight": {
        "keywords": ["insight", "post-mortem", "previous analysis", "historical insight", "prior conclusion"],
        "layers": ["historical_insights"],
        "reason": "Query requests previously derived grounded business insights."
    },
    # 8. Customer Complaints / Cases
    # FIX: also include analytics_snapshots and issue_clusters so root-cause
    # questions get structured operational context, not just raw complaint text.
    "customer_complaint": {
        "keywords": ["not working", "charged", "billing", "top", "slow", "terrible", "problem", "broken", "complaint", "why is", "days now"],
        "layers": ["customer_cases", "conversations", "analytics_snapshots", "issue_clusters"],
        "reason": "Query represents a customer complaint or root-cause investigation ΓÇö pulling cases, snapshots, and clusters."
    }
}


def route_query(query: str, knowledge_docs: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Stage 13: Explainable Query Router.
    Classifies incoming queries into canonical query types and selects target knowledge layers.
    Now uses LLM zero-shot classification if available, with a fast offline keyword fallback.
    """
    clean_q = clean_text(query).lower()
    
    query_type = "root_cause_investigation"
    selected_layers = ["runbooks", "policies", "issue_clusters", "resolved_historical_cases"]
    reason = "Multi-intent query: routing across policies, runbooks, clusters, and resolved precedents for root cause analysis."

    # 1. Removed LLM Routing (per architecture, routing must be deterministic)

    # 2. Offline Fallback: Match intent keywords if LLM routing didn't trigger
    if reason.startswith("Multi-intent query"):
        for q_intent, intent_meta in ROUTER_INTENT_MAP.items():
            if any(kw in clean_q for kw in intent_meta["keywords"]):
                query_type = q_intent
                selected_layers = intent_meta["layers"]
                reason = intent_meta["reason"] + " (Offline Keyword Fallback)"
                break

    filtered_docs = []
    if knowledge_docs:
        filtered_docs = [
            d for d in knowledge_docs
            if (d.get("type") or d.get("document_type")) in selected_layers
        ]
        if not filtered_docs:
            filtered_docs = knowledge_docs

    return {
        "query_type": query_type,
        "selected_layers": selected_layers,
        "reason": reason,
        "route": query_type,  
        "filtered_doc_count": len(filtered_docs),
        "filtered_docs": filtered_docs,
    }
