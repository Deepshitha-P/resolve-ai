"""Resolve-AI FastAPI application and API routes."""

import json
import logging
import os
import threading
import traceback
from typing import Optional

# ── Logging: always print full tracebacks to terminal ──────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("resolve_ai")

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.api_uc18 import router as uc18_router

app = FastAPI(title="Resolve-AI Dashboard API")

app.include_router(uc18_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pipeline Loading State ─────────────────────────────────────────────────────
# The pipeline is loaded in a background thread so the server starts immediately.
# All analytics/KPI endpoints (which only read JSON files) work right away.
# The /api/chat endpoint returns 503 while loading.

pipeline_ctx: dict = {}
_pipeline_loading: bool = False
_pipeline_ready: bool = False
_pipeline_error: Optional[str] = None
_pipeline_progress: str = "Not started"


def _load_pipeline_background():
    """Load the RAG pipeline in a background thread."""
    global pipeline_ctx, _pipeline_loading, _pipeline_ready, _pipeline_error, _pipeline_progress

    _pipeline_loading = True
    _pipeline_progress = "Loading batch context from cache..."
    try:
        from main import run_batch_pipeline_cached
        print("[Startup] Loading RAG Pipeline context in background thread...")
        _pipeline_progress = "Loading cache (pickle + BM25 + ChromaDB + embedder)..."
        pipeline_ctx = run_batch_pipeline_cached(rebuild=False)
        _pipeline_ready = True
        _pipeline_progress = "Ready"
        print("[Startup] RAG Pipeline context loaded successfully!")
    except Exception as exc:
        _pipeline_error = str(exc)
        _pipeline_progress = f"Error: {exc}"
        logger.exception("[Startup] FATAL ERROR loading RAG pipeline")
        print(f"[Startup] ERROR loading RAG pipeline: {exc}")
    finally:
        _pipeline_loading = False


@app.on_event("startup")
def startup_event():
    """Start the pipeline loader in a background thread — server is immediately available."""
    t = threading.Thread(target=_load_pipeline_background, daemon=True, name="pipeline-loader")
    t.start()
    print("[Startup] Server ready. RAG pipeline loading in background thread...")


@app.get("/api/health")
def health():
    """Immediate health check — always responds even during pipeline loading."""
    return {
        "status": "ready" if _pipeline_ready else ("loading" if _pipeline_loading else "error"),
        "pipeline_ready": _pipeline_ready,
        "pipeline_loading": _pipeline_loading,
        "progress": _pipeline_progress,
        "error": _pipeline_error,
    }


@app.get("/api/status")
def status():
    """Detailed status for the frontend loading indicator."""
    return {
        "pipeline_ready": _pipeline_ready,
        "pipeline_loading": _pipeline_loading,
        "progress": _pipeline_progress,
        "error": _pipeline_error,
        "analytics_ready": os.path.exists("data/analytics_v2/metrics_summary.json"),
    }


# ── Persistent Conversation Store ─────────────────────────────────────────
import uuid
from datetime import datetime, timezone

CONVERSATION_HISTORY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "conversation_history.json"
)


class ConversationStore:
    """
    Persistent conversation cache backed by a JSON file.
    
    - Keeps conversations in memory for fast lookups
    - Persists to data/conversation_history.json on every write
    - Loads existing history on startup (survives server restarts)
    - Supports exact-match query cache for deduplication
    """

    def __init__(self, path: str = CONVERSATION_HISTORY_PATH, max_entries: int = 200):
        self.path = path
        self.max_entries = max_entries
        self.conversations: list = []
        self._query_cache: dict = {}  # query string -> response (for dedup)
        self._load()

    def _load(self):
        """Load conversation history from disk on startup."""
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.conversations = json.load(f)
                # Rebuild query cache from loaded history
                for conv in self.conversations:
                    self._query_cache[conv["query"]] = conv["response"]
                print(f"[ConversationStore] Loaded {len(self.conversations)} past conversations from disk.")
            except Exception as e:
                print(f"[ConversationStore] Failed to load history: {e}")
                self.conversations = []

    def _save(self):
        """Persist conversations to disk."""
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.conversations, f, indent=2, default=str, ensure_ascii=False)
        except Exception as e:
            print(f"[ConversationStore] Failed to save history: {e}")

    def get_cached(self, query: str):
        """Return cached response for an exact query match, or None."""
        return self._query_cache.get(query)

    def add(self, query: str, response: dict) -> dict:
        """Add a new conversation entry and persist."""
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "response": response,
        }
        self.conversations.insert(0, entry)  # newest first
        self._query_cache[query] = response

        # Evict oldest if over limit
        if len(self.conversations) > self.max_entries:
            removed = self.conversations.pop()
            self._query_cache.pop(removed["query"], None)

        self._save()
        return entry

    def get_history(self, limit: int = 50) -> list:
        """Return recent conversations (newest first)."""
        return self.conversations[:limit]

    def clear(self):
        """Clear all conversation history."""
        self.conversations = []
        self._query_cache = {}
        self._save()


conversation_store = ConversationStore()


class ChatRequest(BaseModel):
    query: str

@app.post("/api/rag/query")
@app.post("/api/chat")
def chat(request: ChatRequest):
    # Check persistent cache first (works even while pipeline is loading)
    cached = conversation_store.get_cached(request.query)
    if cached is not None:
        print(f"[Cache HIT] query: {request.query}")
        return JSONResponse(
            content=cached,
            media_type="application/json; charset=utf-8",
        )

    # Block if pipeline isn't ready yet
    if not _pipeline_ready:
        if _pipeline_error:
            raise HTTPException(
                status_code=503,
                detail=f"RAG engine failed to load: {_pipeline_error}"
            )
        raise HTTPException(
            status_code=503,
            detail=f"RAG engine is still loading ({_pipeline_progress}). Please wait and try again in a moment."
        )

    try:
        from main import run_query_pipeline
        result = run_query_pipeline(request.query, pipeline_ctx)
        
        # Map evidence_chain from pipeline result to API contract
        evidence_list = []
        for e in result.get("evidence_chain", []):
            evidence_list.append({
                "source_layer": e.get("layer", e.get("source_type", "unknown")),
                "document_id": e.get("doc_id", e.get("source_id", "unknown")),
                "excerpt": (e.get("excerpt", e.get("snippet", e.get("title", ""))) or "")[:300] + "...",
                "retrieval_score": round(float(e.get("relevance_score", e.get("combined_score", 0.0))), 3),
                "confidence": round(float(e.get("trust_score", 0.85)), 2)
            })
            
        insight = result.get("grounded_business_insight", {})

        # Pull real structured fields from stage17 — these are now grounded
        # in query_type, escalation signals, and confidence score (not hardcoded).
        real_actions   = insight.get("recommended_actions") or []
        real_priority  = insight.get("priority", "medium")

        # Fallback only if stage17 didn't populate the field (old cached responses)
        if not real_actions:
            real_actions = ["Review the evidence above and take action per operational runbook.",
                            "Monitor the Analytics dashboard for related volume spikes."]

        # Extract root_causes from insight_text "ROOT CAUSE" section if present
        import re as _re
        insight_text_val = insight.get("insight_text", "")
        root_cause_match = _re.search(
            r"ROOT CAUSE[:\s]+(.*?)(?:\n[A-Z ]{4,}:|\Z)", insight_text_val, _re.DOTALL
        )
        root_causes = []
        if root_cause_match:
            rc_text = root_cause_match.group(1).strip()
            root_causes = [
                line.lstrip("-•* ").strip()
                for line in rc_text.splitlines()
                if line.strip() and not line.strip().startswith("[")
            ][:4]

        # Structure the answer explicitly
        answer = {
            "executive_summary": insight_text_val,
            "key_findings": [],
            "root_causes": root_causes,
            "recommendations": real_actions,
            "priority": real_priority.upper(),
        }
        
        response_content = {
            "query": request.query,
            "query_type": result.get("query_type", "unknown"),
            "target_layers": result.get("selected_layers", []),
            "answer": answer,
            "evidence": evidence_list,
            "grounded": insight.get("is_grounded", True),
            "confidence_score": float(result.get("confidence_score", 0.0)),
        }
        
        # Persist to conversation store (replaces old chat_cache)
        conversation_store.add(request.query, response_content)
        
        return JSONResponse(
            content=response_content,
            media_type="application/json; charset=utf-8",
        )
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/chat/history")
def get_chat_history(limit: int = 50):
    """Return past conversation history (newest first). Persists across restarts."""
    history = conversation_store.get_history(limit=limit)
    return JSONResponse(
        content={"conversations": history, "total": len(conversation_store.conversations)},
        media_type="application/json; charset=utf-8",
    )


@app.delete("/api/chat/history")
def clear_chat_history():
    """Clear all conversation history."""
    conversation_store.clear()
    return {"status": "cleared"}

@app.get("/api/executive-summary")
def get_executive_summary():
    metrics_path = "data/analytics_v2/metrics_summary.json"
    if not os.path.exists(metrics_path):
        return {"error": "Metrics not available"}
        
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)
        
    ds = metrics.get("dataset_metrics", {})
    spikes = metrics.get("emerging_issues", [])
    top_spike = spikes[0] if spikes else {"category": "general issues", "growth_rate_pct": 0}
    
    summary_text = f"{top_spike.get('category', '').replace('_', ' ').title()} complaints are emerging as a major concern, with complaint volume increasing substantially by {top_spike.get('growth_rate_pct', 0)}% during the observed period. Elevated negative sentiment and repeat-contact signals indicate that the issue may require operational investigation."
    
    return {
        "summary": summary_text,
        "key_findings": [
            f"{top_spike.get('category', '').title()} complaints increased significantly.",
            f"Escalation rate is {metrics.get('escalation_metrics', {}).get('escalation_rate', 0) * 100:.2f}%.",
            f"CSAT Proxy is {metrics.get('csat_proxy', {}).get('overall_csat_proxy_score', 0):.2f}/100.",
            f"Repeat-contact rate is {metrics.get('reopen_metrics', {}).get('reopen_rate', 0) * 100:.2f}%."
        ],
        "top_issues": [
            {
                "issue": s.get("category", ""),
                "volume": s.get("recent_7d_volume", 0),
                "growth": s.get("growth_rate_pct", 0),
                "sentiment": "negative",
                "severity": "High priority",
                "csat_proxy": 45.0
            } for s in spikes[:3]
        ],
        "root_causes": ["System degradation", "Unclear policies", "Delivery partner delays"],
        "recommendations": [
            {
                "action": f"Investigate {top_spike.get('category', '')} issues",
                "priority": "HIGH PRIORITY",
                "reason": "Complaint volume increased significantly.",
                "evidence": "DOC-SNAPSHOT-ANALYTICS-V2"
            }
        ],
        "priorities": ["high", "medium"],
        "evidence": ["DOC-SNAPSHOT-ANALYTICS-V2"]
    }


@app.get("/api/executive-summary-v2")
def get_executive_summary_v2():
    """
    Clean executive summary endpoint — every value from real backend data.
    No hardcoded business logic, no invented values.
    """
    metrics_path = "data/analytics_v2/metrics_summary.json"
    temporal_path = "outputs/06_temporal_intelligence.json"

    if not os.path.exists(metrics_path):
        return {"error": "Metrics not available. Run the batch pipeline first."}

    # ── Load real data files ─────────────────────────────────────────────────
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    temporal_signals = []
    if os.path.exists(temporal_path):
        with open(temporal_path, "r", encoding="utf-8") as f:
            temporal_data = json.load(f)
            temporal_signals = temporal_data.get("signals", [])
            active_spikes = temporal_data.get("active_spikes", [])
    else:
        active_spikes = []

    # ── last_analyzed: real file modification time of metrics_summary.json ──
    mtime = os.path.getmtime(metrics_path)
    last_analyzed = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()

    # ── date_start / date_end: real dates from temporal signals ─────────────
    all_days = set()
    for sig in temporal_signals:
        for day in sig.get("daily_counts", {}).keys():
            all_days.add(day)
    sorted_days = sorted(all_days)
    date_start = sorted_days[0] if sorted_days else None
    date_end   = sorted_days[-1] if sorted_days else None
    observation_days = len(sorted_days)

    # ── Core KPI signals (real values, no invented thresholds) ──────────────
    ds  = metrics.get("dataset_metrics", {})
    esc = metrics.get("escalation_metrics", {})
    reop = metrics.get("reopen_metrics", {})
    csat = metrics.get("csat_proxy", {})
    fcr  = metrics.get("first_contact_resolution", {})

    total_conversations   = ds.get("total_conversations", 0)
    negative_sentiment_rt = ds.get("negative_sentiment_rate", 0)
    escalation_rate       = esc.get("escalation_rate", 0)
    reopen_rate           = reop.get("reopen_rate", 0)
    csat_score            = csat.get("overall_csat_proxy_score", 0)
    fcr_rate              = fcr.get("fcr_rate_overall", 0)
    escalated_cases       = esc.get("escalated_cases", 0)
    reopened_cases        = reop.get("reopened_cases", 0)

    # ── Operational signals (real, no invented health formula) ───────────────
    operational_signals = [
        {
            "label": "CSAT Proxy",
            "value": round(csat_score, 2),
            "unit": "/ 100",
            "note": "Deterministic proxy; not a survey score",
            "direction": "lower is worse"
        },
        {
            "label": "Escalation Rate",
            "value": round(escalation_rate * 100, 2),
            "unit": "%",
            "note": f"{escalated_cases} of {total_conversations} conversations escalated",
            "direction": "lower is better"
        },
        {
            "label": "Repeat Contact Rate",
            "value": round(reopen_rate * 100, 2),
            "unit": "%",
            "note": f"{reopened_cases} of {total_conversations} conversations reopened",
            "direction": "lower is better"
        },
        {
            "label": "Negative Sentiment",
            "value": round(negative_sentiment_rt * 100, 2),
            "unit": "%",
            "note": "Share of conversations with negative sentiment",
            "direction": "lower is better"
        },
        {
            "label": "First Contact Resolution",
            "value": round(fcr_rate * 100, 2),
            "unit": "%",
            "note": f"{fcr.get('fcr_cases', 0)} of {total_conversations} resolved on first contact",
            "direction": "higher is better"
        },
    ]

    # ── Key findings: from emerging_issues (backend-ranked by emerging_issue_score) ──
    emerging_issues = metrics.get("emerging_issues", [])
    key_findings = []
    for spike in emerging_issues[:5]:
        cat = spike.get("category", "unknown").replace("_", " ").title()
        growth = spike.get("growth_rate_pct", 0)
        recent_vol = spike.get("recent_7d_volume", 0)
        score = spike.get("emerging_issue_score", 0)
        key_findings.append({
            "category": cat,
            "raw_category": spike.get("category", ""),
            "growth_pct": growth,
            "recent_volume": recent_vol,
            "prior_volume": spike.get("prior_7d_volume", 0),
            "emerging_score": score,
            "signal": f"+{growth:.0f}% · {recent_vol} complaints in recent period",
        })

    # ── Top priority issues: backend category_analysis ordered by escalation_rate desc ──
    # Backend provides per-category: total_cases, escalation_rate, fcr_rate, reopen_rate,
    # avg_sentiment, csat_proxy — no synthetic ranking is created here.
    cat_analysis = metrics.get("category_analysis", {})
    top_categories = cat_analysis.get("top_categories", [])

    # Merge with emerging_issues spike signal if the category has one
    spike_map = {s.get("category", ""): s for s in emerging_issues}

    top_priority_issues = []
    for i, cat in enumerate(top_categories[:5]):
        cat_name = cat.get("category_name", "")
        spike_info = spike_map.get(cat_name)
        top_priority_issues.append({
            "rank": i + 1,
            "category": cat_name.replace("_", " ").title(),
            "raw_category": cat_name,
            "total_cases": cat.get("total_cases", 0),
            "escalation_rate": round(cat.get("escalation_rate", 0) * 100, 2),
            "reopen_rate": round(cat.get("reopen_rate", 0) * 100, 2),
            "fcr_rate": round(cat.get("fcr_rate", 0) * 100, 2),
            "avg_sentiment": round(cat.get("avg_sentiment", 0), 4),
            "csat_proxy": round(cat.get("csat_proxy", 0), 1),
            "is_spike": spike_info is not None,
            "spike_growth_pct": spike_info.get("growth_rate_pct") if spike_info else None,
        })

    # ── Customer impact signals ──────────────────────────────────────────────
    # Highest-escalation category
    highest_esc_cat = max(top_categories, key=lambda c: c.get("escalation_rate", 0), default=None)
    # Highest-reopen category
    highest_reopen_cat = max(top_categories, key=lambda c: c.get("reopen_rate", 0), default=None)
    # Lowest CSAT category
    lowest_csat_cat = min(top_categories, key=lambda c: c.get("csat_proxy", 100), default=None)

    customer_impact = {
        "negative_sentiment_pct": round(negative_sentiment_rt * 100, 2),
        "escalation_pct": round(escalation_rate * 100, 2),
        "repeat_contact_pct": round(reopen_rate * 100, 2),
        "highest_escalation_category": highest_esc_cat.get("category_name", "").replace("_", " ").title() if highest_esc_cat else None,
        "highest_escalation_rate": round(highest_esc_cat.get("escalation_rate", 0) * 100, 2) if highest_esc_cat else None,
        "highest_repeat_category": highest_reopen_cat.get("category_name", "").replace("_", " ").title() if highest_reopen_cat else None,
        "highest_repeat_rate": round(highest_reopen_cat.get("reopen_rate", 0) * 100, 2) if highest_reopen_cat else None,
        "lowest_csat_category": lowest_csat_cat.get("category_name", "").replace("_", " ").title() if lowest_csat_cat else None,
        "lowest_csat_score": round(lowest_csat_cat.get("csat_proxy", 0), 1) if lowest_csat_cat else None,
    }

    # ── Trend overview: real daily aggregation from temporal signals ─────────
    from collections import defaultdict
    daily_vol: dict = defaultdict(int)
    for sig in temporal_signals:
        for day, cnt in sig.get("daily_counts", {}).items():
            daily_vol[day] += cnt

    trend_days = sorted(daily_vol.keys())
    trend_overview = [
        {"date": d, "complaint_count": daily_vol[d]}
        for d in trend_days
    ]

    # ── Recommended actions: one per top spike, linking to RAG ──────────────
    recommended_actions = []
    for spike in emerging_issues[:3]:
        cat = spike.get("category", "").replace("_", " ").title()
        growth = spike.get("growth_rate_pct", 0)
        recommended_actions.append({
            "priority": "HIGH" if growth >= 300 else "MEDIUM",
            "action": f"Investigate {cat} complaint spike",
            "reason": f"{cat} complaints grew by {growth:.0f}% in the recent period.",
            "rag_query": f"What is causing the spike in {cat} complaints and what is the recommended resolution?",
            "evidence_ref": "temporal_intelligence.signals",
        })

    return {
        "total_conversations": total_conversations,
        "date_start": date_start,
        "date_end": date_end,
        "last_analyzed": last_analyzed,
        "observation_days": observation_days,
        "operational_signals": operational_signals,
        "key_findings": key_findings,
        "top_priority_issues": top_priority_issues,
        "customer_impact": customer_impact,
        "trend_overview": trend_overview,
        "recommended_actions": recommended_actions,
        "data_note": (
            "All values derived from the TWCS dataset pipeline output. "
            "Source data dates are historical (2011–2017). "
            "Last analyzed reflects pipeline run time."
        ),
    }



@app.get("/api/dashboard")
def get_dashboard_metrics():
    metrics_path = "data/analytics_v2/metrics_summary.json"
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"error": "Dashboard metrics not generated yet."}


@app.get("/api/reports/date-range")
def get_date_range_report(start: str, end: str):
    try:
        from pipeline.warehouse_engine import WarehouseEngine

        report = WarehouseEngine().run_date_range_report(start, end)
        return JSONResponse(
            content=report,
            media_type="application/json; charset=utf-8",
        )
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/pain-points")
def get_pain_points():
    clusters_path = "outputs/07_issue_clusters.json"

    try:
        if os.path.exists(clusters_path):
            with open(clusters_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = pipeline_ctx.get("clusters", {})

        raw_clusters = data.get("clusters", {})
        if isinstance(raw_clusters, dict):
            cluster_list = list(raw_clusters.values())
        elif isinstance(raw_clusters, list):
            cluster_list = raw_clusters
        else:
            cluster_list = []

        if not cluster_list:
            return {"error": "No clusters found. Run the batch pipeline first.", "clusters": []}

        def pain_score(cluster):
            if "pain_score" in cluster:
                return float(cluster["pain_score"])
            if "pain_point_impact" in cluster:
                return float(cluster["pain_point_impact"].get("pain_score", 0))
            return 0.0

        for cluster in cluster_list:
            cluster["pain_score"] = pain_score(cluster)

        clusters_sorted = sorted(cluster_list, key=pain_score, reverse=True)
        return JSONResponse(
            content={"clusters": clusters_sorted, "total": len(clusters_sorted)},
            media_type="application/json; charset=utf-8",
        )
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load pain points: {exc}")


@app.get("/api/voice-of-customer")
def get_voice_of_customer():
    analytics_path = "outputs/05_analytics.json"
    clusters_path = "outputs/07_issue_clusters.json"
    
    result = {
        "overall_sentiment": {"score": 0, "change": 0, "positive": 0, "neutral": 0, "negative": 0},
        "themes": [],
        "emotional_words": []
    }
    
    try:
        if os.path.exists(analytics_path):
            with open(analytics_path, "r", encoding="utf-8") as f:
                analytics = json.load(f)
                
            dist = analytics.get("sentiment_distribution", {})
            pos = dist.get("positive", 0)
            neu = dist.get("neutral", 0)
            neg = dist.get("negative", 0)
            total = pos + neu + neg
            
            if total > 0:
                result["overall_sentiment"] = {
                    "score": (pos / total) * 100,
                    "change": 0,
                    "positive": round((pos / total) * 100),
                    "neutral": round((neu / total) * 100),
                    "negative": round((neg / total) * 100)
                }
                
        if os.path.exists(clusters_path):
            with open(clusters_path, "r", encoding="utf-8") as f:
                clusters_data = json.load(f)
                
            clusters = clusters_data.get("clusters", {})
            if isinstance(clusters, dict):
                cluster_list = list(clusters.values())
            else:
                cluster_list = clusters
                
            cluster_list.sort(key=lambda x: x.get("volume", 0), reverse=True)
            
            themes = []
            words = {}
            for c in cluster_list[:10]:
                themes.append({
                    "id": str(c.get("cluster_id", "")),
                    "theme": c.get("cluster_name", ""),
                    "sentiment": "negative" if c.get("pain_score", 0) > 50 else "positive",
                    "frequency": c.get("volume", 0),
                    "percentage": c.get("percentage", 0),
                    "quotes": [c.get("summary", "")]
                })
                for kw in c.get("keywords", []):
                    words[kw] = words.get(kw, 0) + c.get("volume", 0)
                    
            result["themes"] = themes
            
            sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)
            result["emotional_words"] = [{"text": w, "value": v, "sentiment": "negative" if v > 50 else "neutral"} for w, v in sorted_words[:30]]
            
        return JSONResponse(content=result, media_type="application/json; charset=utf-8")
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/conversations")
def get_conversations(limit: int = 50):
    conversations_path = "outputs/03_conversations.json"
    try:
        if os.path.exists(conversations_path):
            with open(conversations_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return JSONResponse(content={"conversations": data[:limit]}, media_type="application/json; charset=utf-8")
        return {"conversations": []}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


os.makedirs("frontend", exist_ok=True)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
