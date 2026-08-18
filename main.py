"""
RootIQ -- end-to-end UC18 Analytics-Aware RAG pipeline orchestrator
==================================================================
Runs every stage in order:

RAW DATA -> CLEAN -> CONVERSATIONS -> NLP -> ANALYTICS -> TEMPORAL INTELLIGENCE
-> ISSUE CLUSTERS -> ANALYTICS SNAPSHOTS -> KNOWLEDGE MEMORY -> EMBEDDINGS
-> VECTOR DB -> HYBRID RETRIEVAL -> QUERY ROUTER -> RERANKER -> EVIDENCE
-> CONFIDENCE -> INSIGHT MEMORY -> LLM -> GROUNDED BUSINESS INSIGHT

Usage:
    python main.py
    python main.py --milestone A
    python main.py --milestone B
    python main.py "why is my broadband still down"
    python main.py --rebuild        # force full re-run and refresh cache
"""

import json
import os
import sys
from typing import Any, Dict, List

# -- Load .env before any pipeline imports so env vars are available ----------
try:
    from dotenv import load_dotenv
    _env_file = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path=_env_file, override=False)
except ImportError:
    pass  # python-dotenv not installed; rely on shell env vars

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pipeline"))

from config_loader import load_config
from logger import get_logger
from storage import StorageEngine
from stage01_raw_data import load_and_ingest_raw_data

from stage02_clean import clean_batch, clean_text
from stage03_conversations import build_conversations
from stage04_nlp import enrich_with_nlp, classify_intent, score_sentiment, extract_duration_days, score_severity
from stage05_analytics import compute_analytics
from stage06_temporal_intelligence import compute_temporal_intelligence
from stage07_issue_clusters import cluster_issues
from stage08_analytics_snapshots import build_snapshots
from stage09_knowledge_memory import build_knowledge_memory
from stage10_embeddings import chunk_and_embed_knowledge_memory, embed_knowledge_memory
from stage11_vector_db import ChromaVectorDB, VectorDB
from stage12_hybrid_retrieval import BM25, hybrid_search, hybrid_search_layers, build_layer_index, hybrid_search_precomputed
from stage13_query_router import route_query
from stage14_reranker import rerank
from stage15_evidence_confidence import build_evidence_and_confidence
from stage16_insight_memory import InsightMemory
from stage17_llm_grounded_insight import build_prompt, generate_grounded_insight_template, call_anthropic_llm, generate_policy_grounded_insight

logger = get_logger("MainPipeline")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
# Driven by .env -> USE_REAL_LLM=true to enable live LLM calls
USE_REAL_LLM = os.environ.get("USE_REAL_LLM", "false").lower() in ("true", "1", "yes")


def _save(name: str, obj: Any):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=str)


def run_batch_pipeline(sample_size: int = 1000) -> Dict:
    """Stages 1-9: turn raw dataset cases into structured operational knowledge memory."""
    print("=" * 70)
    print(f"BATCH PIPELINE  (stages 1-9: twcs_cleaned.csv [{sample_size:,} records] -> knowledge memory)")
    print("=" * 70)

    config = load_config()

    # 1. Raw Data Ingestion
    raw = load_and_ingest_raw_data(config=config, limit=sample_size, use_synthetic=False)
    print(f"[1  RAW DATA]              {len(raw):,} raw customer/brand cases ingested")

    # 2. Cleaning
    cleaned = clean_batch(raw)
    print(f"[2  CLEAN]                 text normalized for all {len(cleaned):,} cases")

    # 3. Multi-Turn Conversation Threading
    conversations = build_conversations(cleaned if cleaned else None, config=config)
    if conversations is None:
        import duckdb
        storage = StorageEngine(config)
        conv_parquet = storage.get_parquet_path("conversations.parquet", subfolder="conversations")
        con = duckdb.connect()
        conv_parquet_path = conv_parquet.replace('\\', '/')
        total_conv_count = con.execute(f"SELECT count(*) FROM '{conv_parquet_path}'").fetchone()[0]
        resolved = con.execute(f"SELECT count(*) FROM '{conv_parquet_path}' WHERE has_company_response = true").fetchone()[0]
        print(f"[3  CONVERSATIONS]         {total_conv_count:,} multi-turn threads built ({resolved:,} with company replies)")
    else:
        resolved = sum(1 for c in conversations if c.get("has_company_response"))
        print(f"[3  CONVERSATIONS]         {len(conversations):,} multi-turn threads built ({resolved:,} with company replies)")

    # 4. Local NLP Enrichment
    conversations = enrich_with_nlp(conversations, config=config)
    print(f"[4  LOCAL NLP]             intent/category/severity/emotion/urgency extracted for all threads")

    # 5. DuckDB Analytics
    analytics = compute_analytics(conversations, config=config)
    print(f"[5  DUCKDB ANALYTICS]      Category breakdown: {analytics['by_category']}")

    # 6. Temporal Intelligence
    temporal = compute_temporal_intelligence(conversations, config=config)
    print(f"[6  TEMPORAL INTELLIGENCE] {len(temporal['active_spikes'])} active spike(s) detected")

    # 7. Scalable Issue Clustering (0-100 Pain Score)
    clusters = cluster_issues(conversations, config=config)
    print(f"[7  ISSUE CLUSTERS]        {len(clusters['clusters'])} clusters generated ({len(clusters['incident_candidates'])} potential incidents)")

    # 8. Analytics Snapshots
    snapshots = build_snapshots(analytics, temporal, clusters, config=config)
    print(f"[8  ANALYTICS SNAPSHOTS]   {len(snapshots)} retrievable operational snapshot documents created")

    # 9. Knowledge Memory Assembly
    knowledge_docs = build_knowledge_memory(snapshots=snapshots, conversations=conversations, clusters=clusters, config=config)
    print(f"[9  KNOWLEDGE MEMORY]      {len(knowledge_docs):,} total KnowledgeDocument records indexed")

    # Downstream compatibility mapping: ensure title/text fields exist for stages 10-17
    downstream_docs = []
    for d in knowledge_docs:
        d_copy = dict(d)
        d_copy["doc_id"] = d["document_id"]
        d_copy["type"] = d["document_type"]
        d_copy["title"] = d["document_id"].replace("_", " ")
        d_copy["text"] = d["content"]
        downstream_docs.append(d_copy)

    # 10. Chunk + Embed
    # Documents are split into 500-token windows with 100-token overlap (see .env).
    # LLMAssistedChunker proposes semantic boundaries via the Chunking LLM;
    # falls back to rule-based TextChunker if LLM key is not configured.
    chunked_docs, embedder, doc_vectors = chunk_and_embed_knowledge_memory(downstream_docs)
    print(
        f"[10 EMBEDDINGS]            "
        f"{len(chunked_docs):,} chunks from {len(downstream_docs):,} docs "
        f"(chunk_size={os.environ.get('CHUNK_SIZE',500)}, overlap={os.environ.get('CHUNK_OVERLAP',100)}) "
        f"| TF-IDF matrix {doc_vectors.shape}"
    )

    # 11. ChromaDB Vector Store
    vector_db = ChromaVectorDB()
    if vector_db.is_available:
        vector_db.add(chunked_docs)
        print(f"[11 VECTOR DB]             ChromaDB -- {vector_db.count():,} vectors indexed (persist: {os.environ.get('CHROMA_PERSIST_DIR','./data/chroma_db')})")
    else:
        # Fallback: legacy in-memory VectorDB
        legacy_db = VectorDB()
        legacy_db.add(chunked_docs, doc_vectors)
        vector_db = legacy_db
        print(f"[11 VECTOR DB]             Legacy in-memory -- {legacy_db.count():,} vectors indexed")

    texts = [d["title"] + ". " + d["text"] for d in chunked_docs]
    bm25 = BM25(texts)
    print(f"[12 HYBRID RETRIEVAL]      BM25 index built (vocab size {len(bm25.df)})")

    # Pre-compute per-layer BM25 + doc vectors for fast query-time retrieval
    import time as _layer_t
    _lt0 = _layer_t.time()
    layer_index = build_layer_index(chunked_docs, embedder)
    _lt1 = _layer_t.time()
    print(f"[12 LAYER INDEX]           {len(layer_index)} layers pre-indexed for fast retrieval ({_lt1-_lt0:.2f}s)")

    _save("01_raw_data.json", raw[:100])
    _save("03_conversations.json", conversations[:100])
    _save("05_analytics.json", analytics)
    _save("06_temporal_intelligence.json", temporal)
    _save("07_issue_clusters.json", clusters)
    _save("08_analytics_snapshots.json", snapshots)
    _save("09_knowledge_memory.json", knowledge_docs[:100])

    return {
        "conversations": conversations,
        "knowledge_docs": chunked_docs,      # downstream uses chunked docs
        "raw_knowledge_docs": knowledge_docs,
        "analytics": analytics,
        "temporal": temporal,
        "clusters": clusters,
        "embedder": embedder,
        "doc_vectors": doc_vectors,
        "bm25": bm25,
        "vector_db": vector_db,
        "layer_index": layer_index,
    }


def run_chunked_pipeline(chunk_size: int = 200000):
    """STEP 5: Chunked processing with checkpointing"""
    import time
    from pipeline.mongo_storage import MongoStorageEngine
    
    config = load_config()
    storage = StorageEngine(config)
    checkpoint_file = os.path.join(storage.storage_cfg.get("checkpoints_dir", "data/checkpoints"), "ingest_progress.json")
    
    # Load Checkpoint
    state = {}
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            state = json.load(f)
            
    last_chunk = state.get("last_completed_chunk", -1)
    total_estimated_rows = 2811774
    total_chunks = (total_estimated_rows // chunk_size) + 1
    
    mongo_engine = MongoStorageEngine()
    
    print("=" * 70)
    print(f"CHUNKED PIPELINE: Processing {total_estimated_rows:,} rows in chunks of {chunk_size:,}")
    print("=" * 70)
    
    for chunk_idx in range(last_chunk + 1, total_chunks):
        offset = chunk_idx * chunk_size
        print(f"\n--- Starting Chunk {chunk_idx + 1}/{total_chunks} (Rows {offset:,} to {offset + chunk_size:,}) ---")
        t0 = time.time()
        
        raw = load_and_ingest_raw_data(config=config, limit=chunk_size, use_synthetic=False, offset=offset)
        if not raw:
            print("No more records found. Ingestion complete.")
            break
            
        print(f"[{chunk_idx+1}] Loaded {len(raw):,} raw cases")
        cleaned = clean_batch(raw)
        conversations = build_conversations(cleaned, config=config)
        conversations = enrich_with_nlp(conversations, config=config)
        
        analytics = compute_analytics(conversations, config=config)
        temporal = compute_temporal_intelligence(conversations, config=config)
        clusters = cluster_issues(conversations, config=config)
        
        # Save aggregated outputs to MongoDB
        snapshots = build_snapshots(analytics, temporal, clusters, config=config)
        for snap in snapshots:
            snap["_id"] = f"{snap.get('document_id')}_chunk{chunk_idx}"
            mongo_engine.save_snapshot(snap)
        mongo_engine.save_clusters(clusters.get("clusters", []))
        
        # Write intermediate results to disk
        _save(f"03_conversations_chunk{chunk_idx}.json", conversations[:100])
        _save(f"08_analytics_snapshots_chunk{chunk_idx}.json", snapshots)
        
        # Update checkpoint
        state["last_completed_chunk"] = chunk_idx
        state["rows_processed"] = offset + len(raw)
        with open(checkpoint_file, "w") as f:
            json.dump(state, f)
            
        t1 = time.time()
        elapsed = t1 - t0
        est_total = elapsed * total_chunks
        print(f"--- Chunk {chunk_idx + 1} Complete in {elapsed:.1f}s ---")
        print(f"Estimated time for full dataset: {est_total/60:.1f} minutes")
        
        # STEP 6 constraint: Stop after 1st chunk
        if chunk_idx == 0:
            print("STEP 6: Stopping after first chunk for time estimation.")
            break


# -- Cache path for fast repeat runs ------------------------------------------
_CTX_CACHE = os.path.join(os.path.dirname(__file__), "data", "checkpoints", "ctx_cache.pkl")


def run_batch_pipeline_cached(sample_size: int = 1000, rebuild: bool = False) -> Dict:
    """
    Smart wrapper around run_batch_pipeline.

    First run  : executes all stages 1-12, caches result to disk (~35-45 s).
    Repeat runs: loads the cache from disk in ~1-2 s -- total pipeline ~6 s.
    --rebuild  : forces a full re-run and refreshes the cache.
    """
    import pickle, time

    if not rebuild and os.path.exists(_CTX_CACHE):
        t0 = time.time()
        print("=" * 70)
        print("BATCH PIPELINE  [CACHE HIT] -- loading stages 1-12 from disk")
        print("=" * 70)
        with open(_CTX_CACHE, "rb") as f:
            ctx = pickle.load(f)
        elapsed = time.time() - t0
        # Rebuild BM25 in-memory (not picklable cleanly across Python sessions)
        texts = [d["title"] + ". " + d["text"] for d in ctx["knowledge_docs"]]
        ctx["bm25"] = BM25(texts)
        # Re-attach ChromaDB (already persisted on disk)
        vector_db = ChromaVectorDB()
        # Always set vector_db in ctx — empty DB is handled gracefully downstream
        ctx["vector_db"] = vector_db
        # Reconstruct FastEmbedder (ONNX InferenceSession is not picklable)
        from stage10_embeddings import FastEmbedder, EMBED_MODEL as _EMBED_MODEL
        ctx["embedder"] = FastEmbedder(model_name=os.environ.get("EMBED_MODEL", _EMBED_MODEL))
        
        # Restore or rebuild per-layer index for fast retrieval (BM25 + doc vectors per layer)
        import time as _li_time
        _li0 = _li_time.time()
        layer_index = ctx.get("layer_index")
        # Validate that cached doc_vectors have the same dimension as the
        # reconstructed embedder.  A model change (e.g. bge-small 384-dim
        # → bge-base 768-dim) makes cached vectors unusable and causes the
        # cosine_similarity shape mismatch seen at query time.
        import numpy as _np
        _probe_vec = ctx["embedder"].encode(["probe"])
        _embed_dim = _np.atleast_2d(_probe_vec).shape[1]
        _cache_dim_ok = (
            layer_index
            and all("doc_vectors" in entry for entry in layer_index.values())
            and all(
                _np.atleast_2d(entry["doc_vectors"]).shape[1] == _embed_dim
                for entry in layer_index.values()
                if len(entry["doc_vectors"]) > 0
            )
        )
        if _cache_dim_ok:
            # Instant restore: doc_vectors are already numpy arrays in cache; just recreate BM25
            for entry in layer_index.values():
                if "texts" in entry:
                    entry["bm25"] = BM25(entry["texts"])
            ctx["layer_index"] = layer_index
        else:
            # Dimensions mismatch or missing — rebuild with current embedder
            if layer_index:
                print(f"[CACHE] doc_vector dim mismatch (cached != {_embed_dim}). Rebuilding layer_index.")
            ctx["layer_index"] = build_layer_index(ctx["knowledge_docs"], ctx["embedder"])
            try:
                cache_data = {k: v for k, v in ctx.items() if k not in ("vector_db", "embedder")}
                with open(_CTX_CACHE, "wb") as f:
                    pickle.dump(cache_data, f)
            except Exception:
                pass
        _li1 = _li_time.time()

        n = len(ctx["knowledge_docs"])
        chroma_count = vector_db.count() if vector_db.is_available else 0
        print(f"[1-9  BATCH]  OK {n:,} docs loaded from cache ({elapsed:.2f}s)")
        print(f"[10   EMBED]  OK TF-IDF vectors {ctx['doc_vectors'].shape} restored")
        if chroma_count > 0:
            print(f"[11   CHROMA] OK {chroma_count:,} vectors in ChromaDB")
        else:
            print(f"[11   CHROMA] WARN ChromaDB empty or dimension mismatch -- run with --rebuild to re-index")
        print(f"[12   BM25]   OK BM25 rebuilt (vocab {len(ctx['bm25'].df)})")
        print(f"[12   LAYER]  OK {len(ctx['layer_index'])} layers pre-indexed ({_li1-_li0:.2f}s)")
        return ctx


    # First run or --rebuild: execute all stages
    ctx = run_batch_pipeline(sample_size=sample_size)

    # Persist context
    # Exclude non-picklable objects:
    #   vector_db -> ChromaDB is already persisted on disk, re-attached on load
    #   embedder  -> ONNX InferenceSession cannot be pickled, reconstructed on load
    import pickle
    os.makedirs(os.path.dirname(_CTX_CACHE), exist_ok=True)
    cache_data = {k: v for k, v in ctx.items() if k not in ("vector_db", "embedder")}
    with open(_CTX_CACHE, "wb") as f:
        pickle.dump(cache_data, f)
    print("[CACHE]  OK Batch context saved -- next run will be ~6 seconds")
    return ctx


# -- Query embedding LRU cache ------------------------------------------------
from functools import lru_cache

_query_embed_cache: Dict[str, Any] = {}
_QUERY_CACHE_MAX = 256

def _get_query_embedding(query: str, embedder) -> Any:
    """Cache query embeddings to avoid redundant ONNX calls on repeated queries."""
    import numpy as np
    if query in _query_embed_cache:
        return _query_embed_cache[query]
    vec = embedder.encode([query])
    if hasattr(vec, 'toarray'):
        vec = vec.toarray()
    vec = np.atleast_2d(vec)
    # Evict oldest if cache is full
    if len(_query_embed_cache) >= _QUERY_CACHE_MAX:
        oldest_key = next(iter(_query_embed_cache))
        del _query_embed_cache[oldest_key]
    _query_embed_cache[query] = vec
    return vec


def run_query_pipeline(query: str, ctx: Dict) -> Dict:
    """Stages 13-17: live query -> grounded business insight."""
    import time as _time
    _q_start = _time.time()

    print("\n" + "=" * 70)
    print(f"QUERY PIPELINE  (stages 13-17) -- query: \"{query}\"")
    print("=" * 70)

    _t = _time.time()
    cleaned = clean_text(query)
    intent = classify_intent(cleaned)
    sentiment = score_sentiment(cleaned)
    duration = extract_duration_days(cleaned)
    nlp_signal = {
        "intent": intent,
        "severity": score_severity(intent, sentiment, duration),
        "sentiment_label": "negative" if sentiment < 0 else ("positive" if sentiment > 0 else "neutral"),
        # Change 2: pass trajectory aggregates so Stage 17 prompt gets them
        "trajectory": ctx.get("analytics", {}).get("trajectory_aggregates"),
        "escalation_rate": ctx.get("analytics", {}).get("trajectory_aggregates", {}).get("escalation_rate"),
    }
    print(f"[TIMING] NLP signal:        {_time.time()-_t:.2f}s")

    _t = _time.time()
    routed = route_query(query, ctx["knowledge_docs"])
    print(f"[13 QUERY ROUTER]  query_type='{routed['query_type']}' -> layers={routed['selected_layers']} ({routed['filtered_doc_count']} docs kept)")
    try:
        print(f"                   reason: {routed['reason']}")
    except UnicodeEncodeError:
        safe_reason = routed['reason'].encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        print(f"                   reason: {safe_reason}")
    print(f"[TIMING] Query router:     {_time.time()-_t:.2f}s")

    _t = _time.time()
    routed_docs = routed["filtered_docs"]
    layer_index = ctx.get("layer_index")
    
    if routed["query_type"] == "deep_dive_raw_data":
        print("[13 QUERY ROUTER]  Intercepted Raw Data Deep Dive -> bypassing vector search.")
        from pipeline.warehouse_engine import WarehouseEngine
        engine = WarehouseEngine()
        raw_ev = engine.search_raw_data(query, limit=5)
        hybrid_results = [
            {
                "doc_id": e["doc_id"],
                "combined_score": 0.99,
                "layer": "raw_data_warehouse",
                "doc": {**e, "type": "raw_data_warehouse"}
            } for e in raw_ev
        ]
        print(f"[12 HYBRID RETRIEVAL] Bypassed for Raw Data Loop. Pulled {len(hybrid_results)} raw records.")
    elif layer_index and routed["selected_layers"]:
        # FAST PATH: use pre-computed per-layer BM25 + doc vectors
        # Only encode the query string (~10ms) instead of all docs (~2-5s)
        query_vec = _get_query_embedding(query, ctx["embedder"])
        hybrid_results = hybrid_search_precomputed(
            query, routed["selected_layers"], layer_index, ctx["embedder"],
            top_k=5, alpha=0.5, query_vec=query_vec,
        )
        print(f"[12 HYBRID RETRIEVAL] FAST PATH (precomputed) top result: {hybrid_results[0]['doc_id'] if hybrid_results else 'none'} (score: {hybrid_results[0]['combined_score'] if hybrid_results else 0.0})")
    elif routed_docs:
        # Fallback: re-encodes query + docs together with the
        # same embedder -> guaranteed consistent vector dimensions.
        hybrid_results = hybrid_search_layers(
            query, routed_docs, ctx["embedder"], top_k=5, alpha=0.5
        )
        print(f"[12 HYBRID RETRIEVAL] SLOW PATH top result: {hybrid_results[0]['doc_id'] if hybrid_results else 'none'} (score: {hybrid_results[0]['combined_score'] if hybrid_results else 0.0})")
    else:
        hybrid_results = []
        print("[12 HYBRID RETRIEVAL] top result: none (score: 0.0)")
    print(f"[TIMING] Hybrid retrieval: {_time.time()-_t:.2f}s")

    _t = _time.time()
    reranked = rerank(hybrid_results, query_type=routed["query_type"])
    print(f"[14 RERANKER]      reordered {len(reranked)} candidates by layer-priority + relevance")

    ev = build_evidence_and_confidence(reranked, nlp_signal)
    print(f"[15 EVIDENCE]      {len(ev['evidence_chain'])} evidence items assembled")
    print(f"[15 CONFIDENCE]    {ev['confidence_score']*100:.0f}%")
    print(f"[TIMING] Rerank+Evidence:  {_time.time()-_t:.2f}s")

    # ┌── Fix D: Out-of-core retrieval audit logging ──────────────────
    try:
        import os, json, datetime
        audit_dir = "data/analytics_v2"
        os.makedirs(audit_dir, exist_ok=True)
        audit_path = os.path.join(audit_dir, "retrieval_audit.jsonl")
        
        selected_doc_ids = {e["doc_id"] for e in ev["evidence_chain"]}
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        
        with open(audit_path, "a", encoding="utf-8") as f:
            for rank, r in enumerate(reranked):
                doc_id = r.get("doc_id") or r.get("doc", {}).get("doc_id", "unknown")
                log_entry = {
                    "timestamp": timestamp,
                    "query": query,
                    "query_type": routed["query_type"],
                    "doc_id": doc_id,
                    "document_type": r.get("layer", "unknown"),
                    "retrieval_score": float(r.get("combined_score", 0.0)),
                    "rerank_score": float(r.get("rerank_score", 0.0)),
                    "final_score": float(r.get("rerank_score", 0.0)),
                    "rank": rank + 1,
                    "selected": doc_id in selected_doc_ids
                }
                f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[WARNING] Failed to write retrieval audit log: {e}")

    global_snapshot = next((d for d in ctx["knowledge_docs"] if d.get("doc_id") == "SNAP-GLOBAL" or d.get("document_id") == "SNAP-GLOBAL"), None)
    snapshot_text = global_snapshot["text"] if global_snapshot else "No global snapshot available."

    _t = _time.time()
    # Always route through generate_policy_grounded_insight — it handles USE_REAL_LLM,
    # CloudLLMProvider, offline fallback, and returns the full structured result dict.
    from pipeline.llm_provider import get_generation_llm_provider
    insight = generate_policy_grounded_insight(
        query=query,
        nlp_signal=nlp_signal,
        analytics_snapshot_text=snapshot_text,
        evidence_chain=ev["evidence_chain"],
        confidence=ev["confidence_score"],
        provider=get_generation_llm_provider(),
        query_type=routed["query_type"],
    )
    mode = insight.get("generation_mode", "offline")
    print(f"[17 LLM]           grounded business insight generated (mode={mode}, model={os.environ.get('LLM_MODEL', 'offline')})")
    print(f"[TIMING] LLM insight:      {_time.time()-_t:.2f}s")

    mem = InsightMemory(path=os.path.join(OUTPUT_DIR, "insight_memory.json"))
    mem.save(intent, None, insight)

    prompt = build_prompt(query, nlp_signal, snapshot_text, ev["evidence_chain"], ev["confidence_score"], query_type=routed["query_type"])

    result = {
        "query": query,
        "nlp_signal": nlp_signal,
        "query_type": routed["query_type"],
        "selected_layers": routed["selected_layers"],
        "route_reason": routed["reason"],
        "evidence_chain": ev["evidence_chain"],
        "confidence_score": ev["confidence_score"],
        "prompt_sent_to_llm": prompt,
        "grounded_business_insight": insight,
    }
    _save("17_grounded_insight_result.json", result)

    # P4 — Analytics Overall feedback loop:
    # After each GenAI Agent output, update the Analytics aggregate so the
    # Dashboard KPI snapshot reflects the latest insight signals without
    # requiring a full batch pipeline rebuild.
    _update_analytics_feedback(nlp_signal, ev["confidence_score"], routed["query_type"])

    print(f"[TIMING] -- QUERY PIPELINE TOTAL: {_time.time()-_q_start:.2f}s --")
    return result


def _update_analytics_feedback(nlp_signal: Dict, confidence: float, query_type: str):
    """
    P4 — Analytics Overall feedback loop.

    Appends the current query's NLP signal (sentiment, intent, confidence)
    to the rolling metrics_summary.json.  This closes the loop described
    in the designed architecture: Analytics Overall is updated BOTH by the
    processing layer (Stage 18) AND by GenAI Agent output (this function).

    Lightweight: reads the existing JSON, increments rolling counters, and
    writes back.  No Parquet rebuild, no cache invalidation needed.
    """
    metrics_path = os.path.join("data", "analytics_v2", "metrics_summary.json")
    if not os.path.exists(metrics_path):
        return  # Stage 18 hasn't run yet — nothing to update

    try:
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        # ── Feedback signals ────────────────────────────────────────────
        sentiment_label = nlp_signal.get("sentiment_label", "neutral")
        is_negative = sentiment_label == "negative"
        is_escalated = bool(nlp_signal.get("escalation_rate", 0))

        # Update insight_feedback block (create if absent)
        fb = metrics.setdefault("insight_feedback", {
            "total_queries": 0,
            "negative_queries": 0,
            "escalated_queries": 0,
            "avg_confidence": 0.0,
            "query_type_counts": {},
        })

        prev_total = fb["total_queries"]
        fb["total_queries"]    += 1
        fb["negative_queries"] += int(is_negative)
        fb["escalated_queries"] += int(is_escalated)

        # Rolling average confidence
        fb["avg_confidence"] = float(round(
            (fb["avg_confidence"] * prev_total + float(confidence)) / fb["total_queries"], 4
        ))

        # Query type distribution
        qt_counts = fb.setdefault("query_type_counts", {})
        qt_counts[query_type] = qt_counts.get(query_type, 0) + 1

        # Update negative_sentiment_rate in the top-level KPIs if present
        if "negative_sentiment_rate" in metrics:
            # Recalculate from feedback signal rather than overwriting Stage 18 value
            metrics["insight_feedback"]["live_negative_rate"] = round(
                fb["negative_queries"] / max(fb["total_queries"], 1), 4
            )

        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)

        logger.info(
            f"[P4 Feedback] Analytics updated: query_type={query_type} "
            f"sentiment={sentiment_label} confidence={confidence:.2f} "
            f"total_queries={fb['total_queries']}"
        )

    except Exception as e:
        # Non-fatal: feedback loop failure must never crash the query pipeline
        logger.warning(f"[P4 Feedback] Analytics update failed (non-fatal): {e}")



if __name__ == "__main__":
    import time as _time
    _total_start = _time.time()

    sample_size = 1000
    rebuild_cache = "--rebuild" in sys.argv

    if "--milestone" in sys.argv:
        idx = sys.argv.index("--milestone")
        if idx + 1 < len(sys.argv):
            m_val = sys.argv[idx + 1].upper()
            if m_val == "A":
                sample_size = 1000
            elif m_val == "B":
                sample_size = 50000
            elif m_val == "C":
                sample_size = 2811774

    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            sample_size = int(sys.argv[idx + 1])

    query = "My internet has been down for 3 days now!! No one is helping."
    for arg in sys.argv[1:]:
        if not arg.startswith("--") and arg not in ("A", "B", "C"):
            query = arg

    # -- Use cached pipeline so repeat runs complete in ~1-2 s (not ~40 s) --
    # Pass --rebuild to force a full re-run and refresh the on-disk cache.
    if rebuild_cache:
        import shutil
        chroma_dir = os.environ.get("CHROMA_PERSIST_DIR", "./data/chroma_db")
        if os.path.exists(chroma_dir):
            print(f"[REBUILD] Wiping ChromaDB directory to prevent stale data: {chroma_dir}")
            try:
                shutil.rmtree(chroma_dir)
            except Exception as e:
                print(f"[REBUILD] Failed to wipe ChromaDB (Ensure server.py is stopped!): {e}")

    if "--chunked" in sys.argv:
        run_chunked_pipeline(chunk_size=200000)
        sys.exit(0)

    ctx = run_batch_pipeline_cached(sample_size=sample_size, rebuild=rebuild_cache)
    _batch_elapsed = _time.time() - _total_start
    print(f"[TIMING] -- BATCH PIPELINE:  {_batch_elapsed:.2f}s --")

    result = run_query_pipeline(query, ctx)

    _total_elapsed = _time.time() - _total_start
    print(f"[TIMING] == END-TO-END TOTAL: {_total_elapsed:.2f}s ==")

    print("\n======================================================================")
    print("FINAL GROUNDED BUSINESS INSIGHT")
    print("======================================================================")
    insight_text = result["grounded_business_insight"].get("insight_text", "No insight generated.")
    try:
        print(insight_text)
    except UnicodeEncodeError:
        print(insight_text.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    print(f"\n(Full JSON trace saved under: {OUTPUT_DIR}/)")
