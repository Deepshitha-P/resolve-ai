import os
import json
from typing import Any, Dict, List, Optional
from pipeline.config_loader import load_config
from pipeline.logger import get_logger
from pipeline.schemas import KnowledgeDocument
from pipeline.storage import StorageEngine

logger = get_logger("Stage09_KnowledgeMemory")

def _safe_json_str(val: Any) -> str:
    if val is None:
        return "{}"
    if isinstance(val, str):
        return val
    try:
        return json.dumps(val, default=str)
    except Exception:
        return "{}"


# Operational Runbooks & Policies (Low-Cardinality Standard Knowledge)
DEMO_POLICY_DOCS = [
    {
        "document_id": "DOC-RUNBOOK-NETWORK-001",
        "document_type": "runbooks",
        "title": "Network Node Outage Runbook",
        "content": (
            "When multiple customers in the same area report internet down for more than "
            "a day, first check node-level signal status. A 0% signal reading combined with "
            "clustered complaints in one area indicates a fiber/network node failure, not an "
            "individual customer issue. Escalate immediately to Network Operations for node "
            "inspection. Typical resolution: node restart or fiber splice repair within 4-8 hours."
        ),
        "source_type": "demo_knowledge",
        "topic": "network",
        "intent": "service_outage",
        "severity": "high",
        "metadata": {"category": "network", "type": "runbooks", "layer": "runbooks"}
    },
    {
        "document_id": "DOC-POLICY-REFUND-001",
        "document_type": "policies",
        "title": "Duplicate Charge & Refund Policy",
        "content": (
            "If a customer reports being charged twice or a failed payment where the amount "
            "was still deducted, the standard SLA is to auto-refund within 3-5 business days "
            "after the finance team verifies the duplicate transaction ID. No manual approval "
            "needed for amounts under Rs.2000."
        ),
        "source_type": "demo_knowledge",
        "topic": "payment",
        "intent": "refund",
        "severity": "medium",
        "metadata": {"category": "payment", "type": "policies", "layer": "policies"}
    },
    {
        "document_id": "DOC-POLICY-SLA-001",
        "document_type": "policies",
        "title": "Critical Escalation & Response Policy",
        "content": (
            "Critical severity complaints (negative sentiment + issue duration >= 3 days, or "
            "an active incident affecting 4+ customers in one area) must be escalated to the "
            "relevant operations team within 1 hour and acknowledged to the customer within 2 hours."
        ),
        "source_type": "demo_knowledge",
        "topic": "general",
        "intent": "escalation",
        "severity": "critical",
        "metadata": {"category": "general", "type": "policies", "layer": "policies"}
    },
]


def load_pdf_policies() -> List[Dict]:
    """
    Scans data/policies/ for PDF files, extracts their text using pypdf,
    and returns them as KnowledgeDocument dicts (layer: policies).
    """
    import glob
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.warning("pypdf not installed. Run `pip install pypdf` to ingest PDF policies.")
        return []

    policies_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "policies")
    pdf_files = glob.glob(os.path.join(policies_dir, "*.pdf"))
    
    pdf_docs = []
    for pdf_path in pdf_files:
        try:
            reader = PdfReader(pdf_path)
            text_content = []
            for page in reader.pages:
                text_content.append(page.extract_text() or "")
            
            full_text = "\n".join(text_content).strip()
            if not full_text:
                logger.warning(f"Extracted empty text from {pdf_path}")
                continue

            filename = os.path.basename(pdf_path)
            doc_id = f"DOC-POLICY-PDF-{filename.replace(' ', '_').upper()}"
            
            pdf_docs.append({
                "document_id": doc_id,
                "document_type": "policies",
                "title": f"Custom Policy: {filename}",
                "content": full_text,
                "source_type": "user_pdf",
                "topic": "general",
                "intent": "policy",
                "severity": "medium",
                "metadata": {"category": "general", "type": "policies", "layer": "policies"}
            })
            logger.info(f"Ingested PDF Policy: {filename}")
        except Exception as e:
            logger.error(f"Failed to ingest PDF {pdf_path}: {e}")
            
    return pdf_docs


def _has_resolution_evidence(conv: Dict, nlp: Dict) -> bool:
    """
    Checks for explicit resolution evidence. NEVER fabricates resolution.
    """
    res_signals = nlp.get("resolution_signals") or []
    if isinstance(res_signals, list) and "customer_claimed_resolved" in res_signals:
        return True

    turns = conv.get("turns") or []
    if len(turns) > 1:
        full_text = " ".join([t.get("text", "").lower() for t in turns])
        if any(phrase in full_text for phrase in ["working now", "fixed now", "issue resolved", "thanks for fixing", "refund processed", "resolved"]):
            return True

    return False


def build_knowledge_memory(
    snapshots: Optional[List[Dict]] = None,
    conversations: Optional[List[Dict]] = None,
    clusters: Optional[Dict] = None,
    temporal: Optional[Dict] = None,
    insights: Optional[List[Dict]] = None,
    config: Optional[Dict] = None
) -> List[Dict]:
    """
    Stage 09: 9-Layer Typed Knowledge Memory Architecture.
    Persists each layer separately under data/knowledge/<layer_name>/ using Parquet out-of-core.
    """
    cfg = config or load_config()
    storage = StorageEngine(cfg)
    logger.info("Assembling 9-layer typed knowledge memory architecture out-of-core...")

    low_cardinality_docs: List[Dict] = []
    sample_high_cardinality_docs: List[Dict] = []

    # ---------------------------------------------------------
    # LOW CARDINALITY LAYERS (Persisted + Memory Friendly)
    # ---------------------------------------------------------

    # 1. POLICIES & 2. RUNBOOKS
    policies_docs = []
    runbooks_docs = []
    all_policy_docs = DEMO_POLICY_DOCS + load_pdf_policies()
    for policy_doc in all_policy_docs:
        k_doc = KnowledgeDocument(
            document_id=policy_doc["document_id"],
            doc_id=policy_doc["document_id"],
            document_type=policy_doc["document_type"],
            type=policy_doc["document_type"],
            title=policy_doc["title"],
            text=policy_doc["content"],
            content=policy_doc["content"],
            metadata=policy_doc.get("metadata", {}),
            source_type=policy_doc["source_type"],
            topic=policy_doc.get("topic"),
            intent=policy_doc.get("intent"),
            severity=policy_doc.get("severity"),
        ).model_dump()

        if policy_doc["document_type"] == "policies":
            policies_docs.append(k_doc)
        else:
            runbooks_docs.append(k_doc)
        low_cardinality_docs.append(k_doc)

    storage.write_parquet(policies_docs, "policies.parquet", subfolder="knowledge/policies")
    storage.write_parquet(runbooks_docs, "runbooks.parquet", subfolder="knowledge/runbooks")

    # 3. ANALYTICS SNAPSHOTS
    analytics_docs = []
    if snapshots:
        for s in snapshots:
            k_doc = KnowledgeDocument(
                document_id=s["document_id"],
                doc_id=s["document_id"],
                document_type="analytics_snapshots",
                type="analytics_snapshots",
                title=f"Analytics Snapshot: {s.get('period', 'global')} ({s.get('topic', 'all')})",
                text=s.get("text", str(s.get("metrics", {}))),
                content=s.get("text", str(s.get("metrics", {}))),
                metadata={"period": str(s.get("period", "global")), "topic": str(s.get("topic", "all"))},
                source_type=s.get("source_type", "analytics_engine"),
                topic=s.get("topic"),
                region=s.get("region"),
                period=s.get("period"),
            ).model_dump()
            analytics_docs.append(k_doc)
            low_cardinality_docs.append(k_doc)

    storage.write_parquet(analytics_docs or [{"document_id": "EMPTY", "doc_id": "EMPTY", "document_type": "analytics_snapshots", "type": "analytics_snapshots", "title": "Empty", "text": "empty", "content": "empty", "source_type": "none"}], "analytics_snapshots.parquet", subfolder="knowledge/analytics_snapshots")

    # 4. ISSUE CLUSTERS
    cluster_docs = []
    if clusters and "clusters" in clusters:
        for cid, cl in clusters["clusters"].items():
            pain_score = cl.get("pain_point_impact", {}).get("pain_score", 70)
            content_text = f"Issue Cluster {cl['cluster_name']}: {cl['summary']} Pain score: {pain_score}/100."
            k_doc = KnowledgeDocument(
                document_id=f"DOC-CLUSTER-{cid}",
                doc_id=f"DOC-CLUSTER-{cid}",
                document_type="issue_clusters",
                type="issue_clusters",
                title=f"Issue Cluster: {cl['cluster_name']}",
                text=content_text,
                content=content_text,
                metadata={
                    "cluster_id": str(cid),
                    "cluster_name": str(cl.get("cluster_name")),
                    "pain_score": float(pain_score),
                    "volume": int(cl.get("size", 0)),
                    "dominant_topic": str(cl.get("dominant_topic")),
                    "dominant_area": str(cl.get("dominant_area")),
                },
                source_type="analytics_engine",
                topic=cl.get("dominant_topic"),
                intent=cl.get("dominant_intent"),
                cluster_id=int(cid),
                period=cl.get("period"),
            ).model_dump()
            cluster_docs.append(k_doc)
            low_cardinality_docs.append(k_doc)

    storage.write_parquet(cluster_docs or [{"document_id": "EMPTY", "doc_id": "EMPTY", "document_type": "issue_clusters", "type": "issue_clusters", "title": "Empty", "text": "empty", "content": "empty", "source_type": "none"}], "issue_clusters.parquet", subfolder="knowledge/issue_clusters")

    # 5. TEMPORAL EVENTS
    temporal_docs = []
    if temporal:
        spikes = temporal.get("active_spikes") or []
        for idx, spike in enumerate(spikes):
            t_id = f"DOC-TEMPORAL-{idx+1:03d}"
            content_text = f"Volume surge for {spike.get('category')} on {spike.get('date')}. Count: {spike.get('count')} (z-score: {spike.get('z_score')})."
            k_doc = KnowledgeDocument(
                document_id=t_id,
                doc_id=t_id,
                document_type="temporal_events",
                type="temporal_events",
                title=f"Temporal Spike: {spike.get('category')} on {spike.get('date')}",
                text=content_text,
                content=content_text,
                metadata={
                    "category": str(spike.get("category")),
                    "date": str(spike.get("date")),
                    "count": int(spike.get("count", 0)),
                    "z_score": float(spike.get("z_score", 0.0)),
                },
                source_type="temporal_intelligence",
                topic=spike.get("category"),
                timestamp=spike.get("date"),
            ).model_dump()
            temporal_docs.append(k_doc)
            low_cardinality_docs.append(k_doc)

    storage.write_parquet(temporal_docs or [{"document_id": "EMPTY", "doc_id": "EMPTY", "document_type": "temporal_events", "type": "temporal_events", "title": "Empty", "text": "empty", "content": "empty", "source_type": "none"}], "temporal_events.parquet", subfolder="knowledge/temporal_events")

    # 6. HISTORICAL INSIGHTS
    insights_docs = []
    if insights:
        for ins in insights:
            k_doc = KnowledgeDocument(
                document_id=ins.get("document_id", f"DOC-INSIGHT-{len(insights_docs)+1}"),
                doc_id=ins.get("document_id", f"DOC-INSIGHT-{len(insights_docs)+1}"),
                document_type="historical_insights",
                type="historical_insights",
                title=ins.get("title", "Grounded Historical Insight"),
                text=ins.get("content", ins.get("text", "")),
                content=ins.get("content", ins.get("text", "")),
                metadata={"topic": "grounded_insight"},
                source_type="grounded_llm_insight",
            ).model_dump()
            insights_docs.append(k_doc)
            low_cardinality_docs.append(k_doc)

    storage.write_parquet(insights_docs or [{"document_id": "EMPTY", "doc_id": "EMPTY", "document_type": "historical_insights", "type": "historical_insights", "title": "Empty", "text": "empty", "content": "empty", "source_type": "none"}], "historical_insights.parquet", subfolder="knowledge/historical_insights")

    # ---------------------------------------------------------
    # HIGH CARDINALITY LAYERS (Persisted Out-Of-Core in Batches)
    # ---------------------------------------------------------

    def _get_conv_batches():
        if conversations:
            for i in range(0, len(conversations), 25000):
                yield conversations[i:i + 25000]
        else:
            import duckdb
            conv_file = storage.get_parquet_path("conversations.parquet", subfolder="conversations").replace("\\", "/")
            nlp_file = storage.get_parquet_path("nlp_results.parquet", subfolder="nlp").replace("\\", "/")
            if os.path.exists(conv_file) and os.path.exists(nlp_file):
                con = duckdb.connect()
                offset = 0
                limit = 25000
                while True:
                    rows = con.execute(f"""
                        SELECT c.conversation_id, c.customer_turn_count, c.company_turn_count, c.has_company_response, c.start_time, c.turns,
                               n.intent, n.category, n.subcategory, n.problem_type, n.sentiment, n.sentiment_label, n.emotion, n.urgency,
                               n.severity.label as sev_label, n.escalation_signals, n.resolution_signals, n.temporal_signals,
                               n.entities, n.evidence_spans, n.confidence, n.label_source, n.model_version,
                               n.product, n.region, n.subtype
                        FROM '{conv_file}' c
                        JOIN '{nlp_file}' n ON c.conversation_id = n.conversation_id
                        LIMIT {limit} OFFSET {offset}
                    """).fetchall()
                    if not rows:
                        break
                    batch = []
                    for r in rows:
                        batch.append({
                            "conversation_id": r[0],
                            "customer_turn_count": r[1],
                            "company_turn_count": r[2],
                            "has_company_response": r[3],
                            "start_time": r[4],
                            "turns": r[5],
                            "nlp": {
                                "intent": r[6], "category": r[7], "subcategory": r[8], "problem_type": r[9],
                                "sentiment": r[10], "sentiment_label": r[11], "emotion": r[12], "urgency": r[13],
                                "severity": {"label": r[14]}, "escalation_signals": r[15], "resolution_signals": r[16],
                                "temporal_signals": r[17], "entities": r[18], "evidence_spans": r[19],
                                "confidence": r[20], "label_source": r[21], "model_version": r[22],
                                "product": r[23], "region": r[24], "subtype": r[25]
                            }
                        })
                    yield batch
                    offset += limit


    def _customer_cases_generator():
        for batch in _get_conv_batches():
            chunk = []
            for c in batch:
                conv_id = str(c.get("conversation_id"))
                turns = c.get("turns") or []
                cust_turns = [t for t in turns if t.get("role") == "customer" or t.get("inbound", True)]
                cust_text = cust_turns[0]["text"] if cust_turns else (turns[0]["text"] if turns else "No content")
                nlp = c.get("nlp") or {}

                sev_label = nlp.get("severity", {}).get("label") if isinstance(nlp.get("severity"), dict) else str(nlp.get("severity") or "low")

                case_doc = KnowledgeDocument(
                    document_id=f"DOC-CASE-{conv_id}",
                    doc_id=f"DOC-CASE-{conv_id}",
                    document_type="customer_cases",
                    type="customer_cases",
                    title=f"Customer Case {conv_id} ({nlp.get('category', 'other')})",
                    text=f"Customer complaint {conv_id}: {cust_text}",
                    content=f"Customer complaint {conv_id}: {cust_text}",
                    metadata={
                        "conversation_id": conv_id,
                        "case_id": conv_id,
                        "turn_count": len(turns),
                        "category": str(nlp.get("category", "other")),
                        "subcategory": str(nlp.get("subcategory") or ""),
                        "intent": str(nlp.get("intent", "other")),
                        "problem_type": str(nlp.get("problem_type", "unknown")),
                        "sentiment": float(nlp.get("sentiment", 0.0)) if nlp.get("sentiment") is not None else 0.0,
                        "sentiment_label": str(nlp.get("sentiment_label", "neutral")),
                        "urgency": str(nlp.get("urgency", "low")),
                        "severity": str(sev_label),
                        "escalation_signals": ",".join(nlp.get("escalation_signals", [])) if isinstance(nlp.get("escalation_signals"), list) else str(nlp.get("escalation_signals") or ""),
                        "temporal_signals": ",".join(nlp.get("temporal_signals", [])) if isinstance(nlp.get("temporal_signals"), list) else str(nlp.get("temporal_signals") or ""),
                        "resolution_signals": ",".join(nlp.get("resolution_signals", [])) if isinstance(nlp.get("resolution_signals"), list) else str(nlp.get("resolution_signals") or ""),
                        "entities_json": _safe_json_str(nlp.get("entities")),
                        "evidence_spans_json": _safe_json_str(nlp.get("evidence_spans")),

                        "confidence": float(nlp.get("confidence", 1.0)),
                        "label_source": str(nlp.get("label_source", "local_nlp_provider")),
                        "model_version": str(nlp.get("model_version", "v1.2-local")),
                        "timestamp": str(c.get("start_time") or c.get("created_at") or ""),
                    },
                    source_type=c.get("source_type", "twcs_case"),
                    case_id=conv_id,
                    conversation_id=conv_id,
                    timestamp=c.get("start_time"),
                    topic=nlp.get("category"),
                    intent=nlp.get("intent"),
                    sentiment=nlp.get("sentiment_label"),
                    severity=sev_label,
                ).model_dump()

                chunk.append(case_doc)
                if len(sample_high_cardinality_docs) < 1000:
                    sample_high_cardinality_docs.append(case_doc)
            yield chunk

    def _conversations_generator():
        for batch in _get_conv_batches():
            chunk = []
            for c in batch:
                conv_id = str(c.get("conversation_id"))
                turns = c.get("turns") or []
                cust_turns = [t for t in turns if t.get("role") == "customer" or t.get("inbound", True)]
                cust_text = cust_turns[0]["text"] if cust_turns else (turns[0]["text"] if turns else "No content")
                company_turns = [t for t in turns if t.get("role") == "company" or not t.get("inbound", True)]
                comp_text = company_turns[0]["text"] if company_turns else "No company reply"
                nlp = c.get("nlp") or {}

                full_text = f"Conversation {conv_id} ({c.get('channel', 'twitter')}): Customer: {cust_text}"
                if company_turns:
                    full_text += f" | Company response: {comp_text}"

                sev_label = nlp.get("severity", {}).get("label") if isinstance(nlp.get("severity"), dict) else str(nlp.get("severity") or "low")

                conv_doc = KnowledgeDocument(
                    document_id=f"DOC-CONV-{conv_id}",
                    doc_id=f"DOC-CONV-{conv_id}",
                    document_type="conversations",
                    type="conversations",
                    title=f"Multi-turn Thread {conv_id} ({nlp.get('category', 'other')})",
                    text=full_text,
                    content=full_text,
                    metadata={
                        "conversation_id": conv_id,
                        "turn_count": len(turns),
                        "customer_id": str(c.get("customer_id", "")),
                        "has_company_response": len(company_turns) > 0,
                        "category": str(nlp.get("category", "other")),
                        "subcategory": str(nlp.get("subcategory") or ""),
                        "intent": str(nlp.get("intent", "other")),
                        "problem_type": str(nlp.get("problem_type", "unknown")),
                        "sentiment": float(nlp.get("sentiment", 0.0)) if nlp.get("sentiment") is not None else 0.0,
                        "severity": str(sev_label),
                        "urgency": str(nlp.get("urgency", "low")),
                        "escalation_signals": ",".join(nlp.get("escalation_signals", [])) if isinstance(nlp.get("escalation_signals"), list) else str(nlp.get("escalation_signals") or ""),
                        "entities_json": _safe_json_str(nlp.get("entities")),

                        "timestamp": str(c.get("start_time") or ""),
                    },
                    source_type=c.get("source_type", "twcs_case"),
                    case_id=conv_id,
                    conversation_id=conv_id,
                    timestamp=c.get("start_time"),
                    topic=nlp.get("category"),
                    intent=nlp.get("intent"),
                ).model_dump()

                chunk.append(conv_doc)
            yield chunk

    def _resolved_cases_generator():
        for batch in _get_conv_batches():
            chunk = []
            for c in batch:
                nlp = c.get("nlp") or {}
                if _has_resolution_evidence(c, nlp):
                    conv_id = str(c.get("conversation_id"))
                    turns = c.get("turns") or []
                    cust_turns = [t for t in turns if t.get("role") == "customer" or t.get("inbound", True)]
                    cust_text = cust_turns[0]["text"] if cust_turns else ""
                    company_turns = [t for t in turns if t.get("role") == "company" or not t.get("inbound", True)]
                    comp_text = company_turns[0]["text"] if company_turns else "Resolved"

                    sev_label = nlp.get("severity", {}).get("label") if isinstance(nlp.get("severity"), dict) else str(nlp.get("severity") or "low")

                    res_doc = KnowledgeDocument(
                        document_id=f"DOC-RESOLVED-{conv_id}",
                        doc_id=f"DOC-RESOLVED-{conv_id}",
                        document_type="resolved_historical_cases",
                        type="resolved_historical_cases",
                        title=f"Resolved Case Precedent {conv_id} ({nlp.get('category', 'other')})",
                        text=f"Resolved Issue {conv_id} ({nlp.get('category', 'other')}): Customer: {cust_text} -> Resolution: {comp_text}",
                        content=f"Resolved Issue {conv_id} ({nlp.get('category', 'other')}): Customer: {cust_text} -> Resolution: {comp_text}",
                        metadata={
                            "conversation_id": conv_id,
                            "resolution_evidence": ",".join(nlp.get("resolution_signals", ["explicit_resolution"])) if isinstance(nlp.get("resolution_signals"), list) else str(nlp.get("resolution_signals") or "explicit_resolution"),
                            "category": str(nlp.get("category", "other")),
                            "subcategory": str(nlp.get("subcategory") or ""),
                            "intent": str(nlp.get("intent", "other")),
                            "problem_type": str(nlp.get("problem_type", "unknown")),
                            "sentiment": float(nlp.get("sentiment", 0.0)) if nlp.get("sentiment") is not None else 0.0,
                            "severity": str(sev_label),
                            "timestamp": str(c.get("start_time") or ""),
                        },
                        source_type=c.get("source_type", "twcs_case"),
                        case_id=conv_id,
                        conversation_id=conv_id,
                        topic=nlp.get("category"),
                        intent=nlp.get("intent"),
                    ).model_dump()

                    chunk.append(res_doc)
            yield chunk

    # Stream out-of-core writing to separate parquet subfolders
    total_customer_cases = storage.write_parquet_chunks(_customer_cases_generator(), "customer_cases.parquet", subfolder="knowledge/customer_cases")
    total_conversations = storage.write_parquet_chunks(_conversations_generator(), "conversations.parquet", subfolder="knowledge/conversations")
    total_resolved_cases = storage.write_parquet_chunks(_resolved_cases_generator(), "resolved_historical_cases.parquet", subfolder="knowledge/resolved_historical_cases")

    storage.checkpoint_mgr.save_checkpoint("stage09_knowledge_memory", {
        "customer_cases": total_customer_cases,
        "conversations": total_conversations,
        "resolved_historical_cases": total_resolved_cases,
        "low_cardinality_count": len(low_cardinality_docs),
    })

    logger.info(
        f"[STAGE 9 TYPED KNOWLEDGE MEMORY] Persisted 9 layers out-of-core: "
        f"customer_cases={total_customer_cases}, conversations={total_conversations}, "
        f"resolved_historical_cases={total_resolved_cases}, low_cardinality={len(low_cardinality_docs)}."
    )

    # Return combined list for backward compatibility with downstream RAG stages 10-17
    combined_return = low_cardinality_docs + sample_high_cardinality_docs
    return combined_return


if __name__ == "__main__":
    from stage01_raw_data import generate_raw_complaints
    from stage02_clean import clean_batch
    from stage03_conversations import build_conversations
    from stage04_nlp import enrich_with_nlp

    convs = enrich_with_nlp(build_conversations(clean_batch(generate_raw_complaints(20))))
    kb = build_knowledge_memory(conversations=convs)
    print(f"Generated {len(kb)} knowledge documents for sample return.")
