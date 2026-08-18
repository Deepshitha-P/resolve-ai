import unittest
import os
import shutil
import tempfile
from pipeline.schemas import (
    CaseRecord, Conversation, ConversationTurn, NLPResult, NLPSeverity,
    AnalyticsSnapshot, IssueCluster, PainPointScore, KnowledgeDocument
)
from pipeline.adapters import SyntheticDatasetAdapter, CSVDatasetAdapter
from pipeline.nlp_engine import LocalNLPProvider, ExternalNLPProviderAdapter
from pipeline.storage import StorageEngine, CheckpointManager
from pipeline.stage01_raw_data import load_and_ingest_raw_data
from pipeline.stage02_clean import clean_batch, clean_text
from pipeline.stage03_conversations import build_conversations
from pipeline.stage04_nlp import enrich_with_nlp
from pipeline.stage05_analytics import compute_analytics
from pipeline.stage06_temporal_intelligence import compute_temporal_intelligence
from pipeline.stage07_issue_clusters import cluster_issues
from pipeline.stage08_analytics_snapshots import build_snapshots
from pipeline.stage09_knowledge_memory import build_knowledge_memory
from pipeline.stage10_embeddings import embed_knowledge_memory, LayeredEmbedder
from pipeline.stage11_vector_db import VectorDB, LayeredVectorDB
from pipeline.stage12_hybrid_retrieval import BM25, hybrid_search, hybrid_search_layers
from pipeline.stage13_query_router import route_query
from pipeline.stage14_reranker import rerank
from pipeline.stage15_evidence_confidence import build_evidence_and_confidence
from pipeline.stage16_insight_memory import InsightMemory
from pipeline.stage17_llm_grounded_insight import build_prompt, generate_grounded_insight_template


class TestBlockAImplementation(unittest.TestCase):
    def setUp(self):

        self.test_dir = tempfile.mkdtemp()
        self.config = {
            "dataset": {"raw_csv_path": "data/raw/twcs_cleaned.csv", "source_type": "twcs_case"},
            "storage": {"base_dir": self.test_dir, "chunk_size": 100},
            "nlp": {"default_provider": "local"},
            "temporal": {"spike_z_threshold": 1.0, "min_spike_count": 2},
            "clustering": {"n_clusters": 3, "max_sample_size": 100}
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_canonical_schemas(self):
        sev = NLPSeverity(label="high", score=7, reasons=["financial_impact", "service_failure"])
        nlp = NLPResult(
            intent="payment",
            category="payment",
            sentiment=-0.8,
            sentiment_label="negative",
            emotion="frustration",
            urgency="high",
            severity=sev,
            escalation_signals=["repeat_contact"],
            temporal_signals=["3 days"],
            confidence=0.92
        )
        self.assertEqual(nlp.intent, "payment")
        self.assertEqual(nlp.severity.score, 7)
        self.assertIn("financial_impact", nlp.severity.reasons)

        pain = PainPointScore(
            pain_score=82.4,
            volume_component=0.91,
            negative_sentiment_component=0.84,
            severity_component=0.88,
            growth_component=0.76
        )
        self.assertEqual(pain.pain_score, 82.4)

    def test_02_adapters(self):
        adapter = SyntheticDatasetAdapter()
        data = adapter.load_data(limit=10)
        self.assertEqual(len(data), 10)
        self.assertIsInstance(data[0], CaseRecord)

    def test_03_local_nlp_engine_taxonomy_and_rules(self):
        provider = LocalNLPProvider()

        # Test device_hardware
        res_hw = provider.analyze_text("My phone battery life is terrible and won't charge.")
        self.assertEqual(res_hw.category, "device_hardware")
        self.assertGreaterEqual(res_hw.confidence, 0.90)

        # Test travel_flight
        res_tf = provider.analyze_text("I booked flights for 4 people and my itinerary ticket is incorrect.")
        self.assertEqual(res_tf.category, "travel_flight")
        self.assertGreaterEqual(res_tf.confidence, 0.90)

        # Test store_operations
        res_so = provider.analyze_text("The store staff were unhelpful and items were out of stock.")
        self.assertEqual(res_so.category, "store_operations")
        self.assertGreaterEqual(res_so.confidence, 0.90)

        # Test feature_request
        res_fr = provider.analyze_text("Please add a filter option to export data.")
        self.assertEqual(res_fr.category, "feature_request")
        self.assertGreaterEqual(res_fr.confidence, 0.90)

        # Test improved delivery rules
        res_del = provider.analyze_text("This package was sent to the wrong address via UPS.")
        self.assertEqual(res_del.category, "delivery")

        # Test improved technical_support rules
        res_tech = provider.analyze_text("The new software update breaks core functionality and does not work.")
        self.assertEqual(res_tech.category, "technical_support")

        # Test other fallback and confidence
        res_oth = provider.analyze_text("Hello Becky! Have a great day.")
        self.assertEqual(res_oth.category, "other")
        self.assertIsNone(res_oth.subcategory)  # Insufficient evidence -> MUST BE NULL
        self.assertEqual(res_oth.confidence, 0.55)
        self.assertEqual(res_oth.model_version, "v1.2-local")

    def test_04_external_nlp_adapter_fallback(self):
        adapter = ExternalNLPProviderAdapter()
        # Test valid external JSON
        res_ext = adapter.analyze_json({"intent": {"label": "billing"}, "sentiment": {"label": "negative", "confidence": 0.9}}, raw_text="Overcharged")
        self.assertEqual(res_ext.intent, "billing")
        self.assertEqual(res_ext.label_source, "external_nlp_provider")

        # Test malformed payload forcing fallback
        res_fb = adapter.analyze_json(None, raw_text="Broadband not working")
        self.assertIsNotNone(res_fb.intent)
        self.assertEqual(res_fb.label_source, "local_nlp_provider")

    def test_05_multi_turn_threading(self):
        adapter = SyntheticDatasetAdapter()
        cases = [c.model_dump() for c in adapter.load_data(limit=10)]
        cleaned = clean_batch(cases)
        convs = build_conversations(cleaned, config=self.config)
        self.assertGreater(len(convs), 0)
        self.assertIn("turns", convs[0])
        self.assertIn("first_response_time", convs[0])

    def test_06_analytics_duckdb(self):
        adapter = SyntheticDatasetAdapter()
        cases = [c.model_dump() for c in adapter.load_data(limit=20)]
        convs = enrich_with_nlp(build_conversations(clean_batch(cases), config=self.config), config=self.config)
        analytics = compute_analytics(convs, config=self.config)
        self.assertIn("total_conversations", analytics)
        self.assertIn("negative_sentiment_rate", analytics)
        self.assertIsNone(analytics["sla_target"])
        self.assertIsNone(analytics["sla_breach"])

    def test_07_temporal_intelligence(self):
        adapter = SyntheticDatasetAdapter()
        cases = [c.model_dump() for c in adapter.load_data(limit=30)]
        convs = enrich_with_nlp(build_conversations(clean_batch(cases), config=self.config), config=self.config)
        temp = compute_temporal_intelligence(convs, config=self.config)
        self.assertIn("signals", temp)
        self.assertIn("active_spikes", temp)

    def test_08_issue_clusters_explainable_pain_score(self):
        adapter = SyntheticDatasetAdapter()
        cases = [c.model_dump() for c in adapter.load_data(limit=30)]
        convs = enrich_with_nlp(build_conversations(clean_batch(cases), config=self.config), config=self.config)
        clusters = cluster_issues(convs, config=self.config)
        self.assertIn("clusters", clusters)
        first_cl = list(clusters["clusters"].values())[0]
        pain_impact = first_cl["pain_point_impact"]
        self.assertIn("pain_score", pain_impact)
        self.assertIn("volume_component", pain_impact)

    def test_09_knowledge_documents(self):
        adapter = SyntheticDatasetAdapter()
        cases = [c.model_dump() for c in adapter.load_data(limit=20)]
        convs = enrich_with_nlp(build_conversations(clean_batch(cases), config=self.config), config=self.config)
        analytics = compute_analytics(convs, config=self.config)
        temp = compute_temporal_intelligence(convs, config=self.config)
        clusters = cluster_issues(convs, config=self.config)
        snaps = build_snapshots(analytics, temp, clusters, config=self.config)
        
        kb_docs = build_knowledge_memory(snapshots=snaps, conversations=convs, clusters=clusters, config=self.config)
        self.assertGreater(len(kb_docs), 0)
        self.assertIn(kb_docs[0]["document_type"], ["runbooks", "runbook"])


    def test_10_storage_and_checkpoints(self):
        storage = StorageEngine(self.config)
        storage.write_parquet([{"id": 1, "val": "test"}], "test.parquet")
        res = storage.read_parquet("test.parquet")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["val"], "test")

    def test_11_nlp_v12_hierarchical_subcategories_and_entities(self):
        provider = LocalNLPProvider()

        # 1. Subcategory & Problem Type test
        res1 = provider.analyze_text("My broadband internet is down and disconnected for 3 days.")
        self.assertEqual(res1.category, "network")
        self.assertEqual(res1.subcategory, "internet_down")
        self.assertEqual(res1.intent, "internet_down")
        self.assertEqual(res1.problem_type, "service_failure")
        self.assertIn("3 days", res1.temporal_signals)
        self.assertIn("broadband", res1.entities.get("product_service", ""))
        self.assertEqual(res1.entities.get("duration"), "3 days")

        # 2. Insufficient evidence -> subcategory MUST be None
        res2 = provider.analyze_text("I have a general question regarding wifi.")
        self.assertEqual(res2.category, "network")
        self.assertIsNone(res2.subcategory)
        self.assertEqual(res2.intent, "network")

        # 3. Entity Extraction (Amount, Currency, Order ID, Location)
        res3 = provider.analyze_text("I was charged $50 twice for order #TW-987654 in Anna Nagar store!")
        self.assertEqual(res3.category, "payment")
        self.assertEqual(res3.subcategory, "duplicate_charge")
        self.assertEqual(res3.problem_type, "payment_failure")
        self.assertEqual(res3.entities.get("amount"), "$50")
        self.assertEqual(res3.entities.get("currency"), "USD")
        self.assertEqual(res3.entities.get("order_reference_id"), "#TW-987654")
        self.assertEqual(res3.entities.get("location"), "anna nagar")

        # 4. Resolution signals
        res4 = provider.analyze_text("Sent several tweets, still not working! Please fix it, waiting for reply.")
        self.assertIn("customer_claimed_unresolved", res4.resolution_signals)
        self.assertIn("waiting_for_response", res4.resolution_signals)
        self.assertIn("repeat_contact", res4.escalation_signals)

    def test_12_customer_company_separation_regression(self):
        # Proves company replies are NOT classified as customer complaints
        provider = LocalNLPProvider()

        # Company reply text typically sent by brand reps
        company_reply_text = "Please DM us your order ID so our team can assist you further."
        res_comp = provider.analyze_text(company_reply_text)
        
        # Verify model version and confidence
        self.assertEqual(res_comp.model_version, "v1.2-local")

        # Check conversation stage filtering:
        # Build synthetic conversation with customer turn followed by company turn
        conv = {
            "conversation_id": "CONV-TEST-001",
            "turns": [
                {"turn_id": "1", "role": "customer", "inbound": True, "text": "My internet is down!"},
                {"turn_id": "2", "role": "company", "inbound": False, "text": "Please DM us your account number."}
            ]
        }
        enriched_list = enrich_with_nlp([conv], config=self.config)
        self.assertEqual(enriched_list[0]["nlp"]["category"], "network")
        self.assertEqual(enriched_list[0]["nlp"]["subcategory"], "internet_down")
        # Ensure company turn text ("Please DM us...") was NOT evaluated as the primary complaint text
        self.assertNotEqual(enriched_list[0]["nlp"]["intent"], "store_operations")

    def test_13_typed_knowledge_memory_architecture(self):
        # 1. Prepare synthetic test conversations: 1 unresolved, 1 resolved
        conv_unresolved = {
            "conversation_id": "CONV-UNRES-001",
            "start_time": "2026-08-14T10:00:00Z",
            "turns": [
                {"turn_id": "101", "role": "customer", "inbound": True, "text": "My broadband internet is down and slow for 3 days!"},
                {"turn_id": "102", "role": "company", "inbound": False, "text": "We are looking into this."}
            ]
        }
        conv_resolved = {
            "conversation_id": "CONV-RES-002",
            "start_time": "2026-08-14T11:00:00Z",
            "turns": [
                {"turn_id": "201", "role": "customer", "inbound": True, "text": "I was charged twice $50 for order #TW-12345!"},
                {"turn_id": "202", "role": "company", "inbound": False, "text": "Refund processed and issue resolved. Thanks!"}
            ]
        }

        convs = enrich_with_nlp([conv_unresolved, conv_resolved], config=self.config)

        # Build 9-layer typed knowledge memory
        storage = StorageEngine(self.config)
        docs = build_knowledge_memory(conversations=convs, config=self.config)

        # 2. Check persistence of high-cardinality layers out-of-core
        cust_cases = storage.read_parquet("customer_cases.parquet", subfolder="knowledge/customer_cases")
        conversations_layer = storage.read_parquet("conversations.parquet", subfolder="knowledge/conversations")
        resolved_layer = storage.read_parquet("resolved_historical_cases.parquet", subfolder="knowledge/resolved_historical_cases")

        self.assertEqual(len(cust_cases), 2)
        self.assertEqual(len(conversations_layer), 2)
        # Explicit resolution: ONLY 1 resolved case (conv_resolved)
        self.assertEqual(len(resolved_layer), 1)
        self.assertEqual(resolved_layer[0]["conversation_id"], "CONV-RES-002")

        # 3. Check low-cardinality layers
        policies_layer = storage.read_parquet("policies.parquet", subfolder="knowledge/policies")
        runbooks_layer = storage.read_parquet("runbooks.parquet", subfolder="knowledge/runbooks")
        self.assertGreater(len(policies_layer), 0)
        self.assertGreater(len(runbooks_layer), 0)

        # 4. Check metadata & provenance preservation
        unres_meta = cust_cases[0]["metadata"]
        self.assertEqual(unres_meta["conversation_id"], "CONV-UNRES-001")
        self.assertEqual(unres_meta["category"], "network")
        self.assertEqual(unres_meta["subcategory"], "internet_down")
        self.assertEqual(unres_meta["problem_type"], "service_failure")
        self.assertEqual(unres_meta["model_version"], "v1.2-local")

        # 5. Verify customer/company separation in doc text
        self.assertIn("Customer complaint CONV-UNRES-001: My broadband internet is down", cust_cases[0]["text"])
        self.assertNotIn("We are looking into this", cust_cases[0]["text"])

    def test_14_typed_rag_retrieval_architecture(self):
        # 1. Test Query Routing across at least 6 query types
        r_complaint = route_query("my internet is down and slow")
        self.assertEqual(r_complaint["query_type"], "customer_complaint")
        self.assertEqual(r_complaint["selected_layers"], ["customer_cases", "conversations"])

        r_precedent = route_query("how was duplicate charge resolved precedent")
        self.assertEqual(r_precedent["query_type"], "historical_precedent")
        self.assertEqual(r_precedent["selected_layers"], ["resolved_historical_cases"])

        r_incident = route_query("widespread outage incident cluster")
        self.assertEqual(r_incident["query_type"], "incident")
        self.assertEqual(r_incident["selected_layers"], ["issue_clusters"])

        r_trend = route_query("volume surge spike on monday")
        self.assertEqual(r_trend["query_type"], "temporal_spike")
        self.assertEqual(r_trend["selected_layers"], ["temporal_events"])

        r_policy = route_query("auto-refund SLA policy rule")
        self.assertEqual(r_policy["query_type"], "policy")
        self.assertEqual(r_policy["selected_layers"], ["policies"])

        r_runbook = route_query("node outage troubleshooting runbook SOP")
        self.assertEqual(r_runbook["query_type"], "operational_procedure")
        self.assertEqual(r_runbook["selected_layers"], ["runbooks"])

        # 2. Build test knowledge memory with all 9 layers
        conv_res = {
            "conversation_id": "CONV-RESOLVED-100",
            "start_time": "2026-08-14T10:00:00Z",
            "turns": [
                {"turn_id": "1", "role": "customer", "inbound": True, "text": "Charged twice $50 for order #TW-999!"},
                {"turn_id": "2", "role": "company", "inbound": False, "text": "Refund processed and issue resolved."}
            ]
        }
        convs = enrich_with_nlp([conv_res], config=self.config)
        knowledge_docs = build_knowledge_memory(conversations=convs, config=self.config)

        # 3. Layer Filtering & No Cross-Layer Contamination Test
        r_pol = route_query("auto-refund policy rule", knowledge_docs)
        for d in r_pol["filtered_docs"]:
            self.assertEqual(d["type"], "policies")
            self.assertNotEqual(d["type"], "customer_cases")

        # 4. Historical Resolution Retrieval Test
        r_prec = route_query("refunded duplicate charge precedent", knowledge_docs)
        self.assertEqual(r_prec["selected_layers"], ["resolved_historical_cases"])
        storage = StorageEngine(self.config)
        resolved_docs = storage.read_parquet("resolved_historical_cases.parquet", subfolder="knowledge/resolved_historical_cases")
        self.assertEqual(len(resolved_docs), 1)
        self.assertEqual(resolved_docs[0]["conversation_id"], "CONV-RESOLVED-100")

        # 5. Hybrid Retrieval, Reranking & Provenance Preservation
        embedder, _ = embed_knowledge_memory(knowledge_docs)
        hybrid_res = hybrid_search_layers("auto-refund SLA policy", r_pol["filtered_docs"], embedder, top_k=3)
        self.assertGreater(len(hybrid_res), 0)
        reranked = rerank(hybrid_res)
        self.assertIn("rerank_score", reranked[0])
        self.assertIn("layer", reranked[0])

        ev = build_evidence_and_confidence(reranked, {"severity": "medium"})
        self.assertGreater(len(ev["evidence_chain"]), 0)
        self.assertEqual(ev["evidence_chain"][0]["layer"], "policies")

        # 6. Evidence Citation Test in LLM synthesis
        insight = generate_grounded_insight_template("auto-refund SLA policy", {"severity": "medium", "intent": "refund"}, "Global context", ev["evidence_chain"], ev["confidence_score"])
        self.assertEqual(insight["status"], "sufficient_evidence")
        self.assertIn("Supported by:", insight["insight_text"])
        self.assertIn("DOC-POLICY-REFUND-001", insight["insight_text"])

        # 7. Insufficient Evidence Behavior Test
        empty_ev = build_evidence_and_confidence([], {"severity": "low"})
        self.assertEqual(empty_ev["confidence_score"], 0.0)
        insufficient_insight = generate_grounded_insight_template("unknown alien query", {"severity": "low", "intent": "other"}, "Global context", empty_ev["evidence_chain"], empty_ev["confidence_score"])
        self.assertEqual(insufficient_insight["status"], "insufficient_evidence")
        self.assertIn("Insufficient evidence in knowledge base", insufficient_insight["insight_text"])


if __name__ == "__main__":
    unittest.main()



