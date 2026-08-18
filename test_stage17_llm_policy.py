"""
test_stage17_llm_policy.py

Focused unit test suite for Stage 17 Policy-Aware Configurable LLM Provider Architecture.
Covers all 20 required scenarios specified in UC18 requirements (using mocks; no paid API key required).
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

project_root = os.getcwd()
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "pipeline"))

from pipeline.llm_provider import LLMProvider, LocalLLMProvider, CloudLLMProvider, get_llm_provider
from pipeline.policy_taxonomy import find_company_policy_family, COMPANY_POLICY_FAMILIES
from pipeline.stage17_llm_grounded_insight import (
    build_prompt,
    generate_policy_grounded_insight,
    generate_grounded_insight_template
)


class TestStage17LLMPolicy(unittest.TestCase):

    def setUp(self):
        self.mock_evidence = [
            {
                "doc_id": "DOC-POLICY-REFUND-001",
                "source_id": "DOC-POLICY-REFUND-001",
                "layer": "policies",
                "title": "AmazonHelp Refund Policy",
                "excerpt": "Standard refund eligibility requires return verification within 30 days.",
                "relevance_score": 0.88,
                "trust_score": 0.90,
                "metadata": {"company": "AmazonHelp", "policy_family": "Returns & Refunds", "product": "unknown", "region": "unknown"}
            },
            {
                "doc_id": "DOC-RUNBOOK-NETWORK-001",
                "source_id": "DOC-RUNBOOK-NETWORK-001",
                "layer": "runbooks",
                "title": "Network Node Outage Runbook",
                "excerpt": "Check node-level signal status; if 0% signal, escalate to Network Operations.",
                "relevance_score": 0.85,
                "trust_score": 0.95,
                "metadata": {"company": "Comcast", "product": "internet", "region": "unknown"}
            }
        ]

    # Test 1: Cloud provider initialization
    def test_01_cloud_provider_initialization(self):
        provider = CloudLLMProvider(provider="anthropic", model="claude-sonnet-4-6", api_key="sk-test-key")
        self.assertEqual(provider.provider, "anthropic")
        self.assertEqual(provider.model, "claude-sonnet-4-6")
        self.assertEqual(provider.api_key, "sk-test-key")

    # Test 2: Cloud provider configuration via env
    def test_02_cloud_provider_config(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "LLM_MODEL": "gpt-4o", "LLM_API_KEY": "sk-env-key"}):
            provider = get_llm_provider()
            self.assertIsInstance(provider, CloudLLMProvider)
            self.assertEqual(provider.provider, "openai")
            self.assertEqual(provider.model, "gpt-4o")

    # Test 3: Missing API key handling
    def test_03_missing_api_key(self):
        provider = CloudLLMProvider(provider="anthropic", api_key="")
        resp = provider.generate("Test prompt")
        # Must fallback gracefully to LocalLLMProvider
        self.assertIn("Test prompt", resp)

    # Test 4: Cloud provider failure handling
    @patch("urllib.request.urlopen")
    def test_04_cloud_provider_failure(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("API Timeout")
        provider = CloudLLMProvider(provider="anthropic", api_key="sk-test-key")
        resp = provider.generate("Test prompt")
        # Must catch exception and fallback
        self.assertIsNotNone(resp)

    # Test 5: Cloud -> Local fallback
    def test_05_cloud_to_local_fallback(self):
        provider = CloudLLMProvider(provider="anthropic", api_key=None)
        res = generate_policy_grounded_insight(
            query="My refund is still pending. What should support check?",
            nlp_signal={"intent": "refund", "severity": "medium"},
            analytics_snapshot_text="Global snapshot",
            evidence_chain=self.mock_evidence,
            confidence=0.85,
            provider=provider
        )
        self.assertEqual(res["status"], "sufficient_evidence")

    # Test 6: Grounded complaint answer format
    def test_06_grounded_complaint_answer(self):
        res = generate_policy_grounded_insight(
            query="My refund is still pending. What should support check?",
            nlp_signal={"intent": "refund", "severity": "medium"},
            analytics_snapshot_text="Global snapshot",
            evidence_chain=self.mock_evidence,
            confidence=0.85
        )
        self.assertIn("Observed Complaint Evidence:", res["insight_text"])
        self.assertIn("Recommended Support Action:", res["insight_text"])

    # Test 7: Insufficient evidence handling (Query 6)
    def test_07_insufficient_evidence(self):
        res = generate_policy_grounded_insight(
            query="What is the capital of Mars?",
            nlp_signal={"intent": "general", "severity": "low"},
            analytics_snapshot_text="",
            evidence_chain=[],
            confidence=0.0
        )
        self.assertEqual(res["status"], "insufficient_evidence")
        self.assertIn("Insufficient evidence", res["insight_text"])

    # Test 8: Evidence citation preservation
    def test_08_evidence_citation_preservation(self):
        res = generate_policy_grounded_insight(
            query="What is the refund policy for AmazonHelp?",
            nlp_signal={"intent": "refund", "severity": "low"},
            analytics_snapshot_text="",
            evidence_chain=self.mock_evidence,
            confidence=0.88
        )
        self.assertIn("DOC-POLICY-REFUND-001", res["insight_text"])
        self.assertGreater(len(res["citations"]), 0)

    # Test 9: No fabricated document IDs
    def test_09_no_fabricated_doc_ids(self):
        res = generate_policy_grounded_insight(
            query="What is the refund policy?",
            nlp_signal={"intent": "refund", "severity": "low"},
            analytics_snapshot_text="",
            evidence_chain=self.mock_evidence,
            confidence=0.85
        )
        for citation in res["citations"]:
            self.assertIn(citation["doc_id"], ["DOC-POLICY-REFUND-001", "DOC-RUNBOOK-NETWORK-001"])

    # Test 10: Policy question handling (Query 2)
    def test_10_policy_question_handling(self):
        res = generate_policy_grounded_insight(
            query="What is the refund policy for this company?",
            nlp_signal={"intent": "refund", "severity": "medium"},
            analytics_snapshot_text="",
            evidence_chain=self.mock_evidence,
            confidence=0.88
        )
        self.assertIn("Policy Answer", res["insight_text"])
        self.assertIn("Company:", res["insight_text"])
        self.assertIn("Policy Family:", res["insight_text"])

    # Test 11: Company-specific policy routing
    def test_11_company_specific_policy_routing(self):
        match = find_company_policy_family("What is the refund policy for AmazonHelp?")
        self.assertEqual(match["company"], "AmazonHelp")
        self.assertEqual(match["policy_family"], "Returns & Refunds")

        match_apple = find_company_policy_family("My iPhone hardware screen is broken on AppleSupport")
        self.assertEqual(match_apple["company"], "AppleSupport")
        self.assertEqual(match_apple["policy_family"], "Device & Hardware")

    # Test 12: Historical inferred policy labeling
    def test_12_historical_inferred_policy_labeling(self):
        res = generate_policy_grounded_insight(
            query="What is the refund policy?",
            nlp_signal={"intent": "refund", "severity": "low"},
            analytics_snapshot_text="",
            evidence_chain=self.mock_evidence,
            confidence=0.85
        )
        self.assertEqual(res["authoritativeness"], "inferred")
        self.assertEqual(res["provenance"], "historical_inference")
        self.assertIn("Historical Inferred Policy", res["insight_text"])

    # Test 13: Conflicting policy evidence (Query 7)
    def test_13_conflicting_policy_evidence(self):
        conflicting_evidence = [
            {
                "doc_id": "DOC-POLICY-A",
                "layer": "policies",
                "title": "Refund Rule A",
                "excerpt": "Refund processed within 7 days.",
                "relevance_score": 0.90,
                "trust_score": 0.80
            },
            {
                "doc_id": "DOC-POLICY-B",
                "layer": "policies",
                "title": "Refund Rule B",
                "excerpt": "Refund processed within 14 days.",
                "relevance_score": 0.88,
                "trust_score": 0.80
            }
        ]
        res = generate_policy_grounded_insight(
            query="What happens if the historical policy evidence conflicts?",
            nlp_signal={"intent": "refund", "severity": "medium"},
            analytics_snapshot_text="",
            evidence_chain=conflicting_evidence,
            confidence=0.85
        )
        self.assertTrue(res["conflicting_evidence"])
        self.assertIn("CONFLICTING HISTORICAL EVIDENCE", res["insight_text"])

    # Test 14: Unknown product handling
    def test_14_unknown_product_handling(self):
        unknown_evidence = [
            {
                "doc_id": "DOC-POLICY-REFUND-001",
                "layer": "policies",
                "title": "Refund Policy",
                "excerpt": "Refunds subject to terms.",
                "relevance_score": 0.85,
                "metadata": {"product": "unknown", "region": "unknown"}
            }
        ]
        res = generate_policy_grounded_insight(
            query="What is the refund policy?",
            nlp_signal={"intent": "refund", "severity": "low"},
            analytics_snapshot_text="",
            evidence_chain=unknown_evidence,
            confidence=0.85
        )
        self.assertEqual(res["product"], "unknown")

    # Test 15: Unknown region handling
    def test_15_unknown_region_handling(self):
        res = generate_policy_grounded_insight(
            query="What is the refund policy?",
            nlp_signal={"intent": "refund", "severity": "low"},
            analytics_snapshot_text="",
            evidence_chain=self.mock_evidence,
            confidence=0.85
        )
        self.assertEqual(res["region"], "unknown")

    # Test 16: Analytics V2 question handling (Query 4 & 5)
    def test_16_analytics_v2_question(self):
        res = generate_policy_grounded_insight(
            query="What is our escalation rate?",
            nlp_signal={"intent": "analytics", "severity": "low"},
            analytics_snapshot_text="Global escalation rate: 8.71%",
            evidence_chain=self.mock_evidence,
            confidence=0.90
        )
        self.assertIn("EXECUTIVE SUMMARY", res["insight_text"])
        self.assertIn("KEY FINDINGS", res["insight_text"])
        self.assertIn("8.71%", res["insight_text"])

    # Test 17: CSAT Proxy labeling
    def test_17_csat_proxy_labeling(self):
        res = generate_policy_grounded_insight(
            query="Why is the CSAT Proxy low?",
            nlp_signal={"intent": "analytics", "severity": "high"},
            analytics_snapshot_text="CSAT Proxy is 47.08/100",
            evidence_chain=self.mock_evidence,
            confidence=0.90
        )
        self.assertIn("CSAT Proxy", res["insight_text"])
        self.assertNotIn("survey CSAT score of", res["insight_text"].lower())

    # Test 18: Runbook question handling (Query 3)
    def test_18_runbook_question_handling(self):
        res = generate_policy_grounded_insight(
            query="My internet has been down for three days. What should support do?",
            nlp_signal={"intent": "internet_down", "severity": "high"},
            analytics_snapshot_text="",
            evidence_chain=self.mock_evidence,
            confidence=0.92
        )
        self.assertIn("Recommended Support Action:", res["insight_text"])
        self.assertIn("DOC-RUNBOOK-NETWORK-001", res["insight_text"])

    # Test 19: Recommendation grounding
    def test_19_recommendation_grounding(self):
        res = generate_policy_grounded_insight(
            query="My internet has been down for three days. What should support do?",
            nlp_signal={"intent": "internet_down", "severity": "high"},
            analytics_snapshot_text="",
            evidence_chain=self.mock_evidence,
            confidence=0.92
        )
        self.assertIn("DOC-RUNBOOK-NETWORK-001", res["insight_text"])
        self.assertIn("Supported by:", res["insight_text"])

    # Test 20: LLM receives only retrieved evidence payload
    def test_20_prompt_payload_bounded(self):
        prompt = build_prompt(
            query="What is the refund policy?",
            nlp_signal={"intent": "refund", "severity": "low"},
            analytics_snapshot_text="Global snapshot text",
            evidence_chain=self.mock_evidence,
            confidence=0.85
        )
        self.assertIn("DOC-POLICY-REFUND-001", prompt)
        self.assertIn("DOC-RUNBOOK-NETWORK-001", prompt)
        self.assertNotIn("conversations.parquet", prompt)
        self.assertLess(len(prompt), 5000)  # Bounded size


if __name__ == "__main__":
    unittest.main()
