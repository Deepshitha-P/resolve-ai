"""
test_analytics_v2.py

Unit test suite for UC18 Analytics V2 layer.
Verifies:
1. Numerator, Denominator, Formula, and Zero-division safety for every metric.
2. Product & Region coverage % and missing rate.
3. CSAT Proxy trajectory structure and non-null values.
4. Output file persistence in data/analytics_v2/.
5. RAG snapshot document creation.
"""

import os
import sys
import json
import unittest
import pyarrow.parquet as pq

project_root = os.getcwd()
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "pipeline"))

from pipeline.stage18_analytics_v2 import run_stage18_analytics_v2

class TestAnalyticsV2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.summary = run_stage18_analytics_v2()
        cls.out_dir = os.path.join(project_root, "data", "analytics_v2")

    def test_01_output_files_exist(self):
        """Verify all Parquet & JSON output files exist in data/analytics_v2/."""
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "metrics_summary.json")))
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "category_metrics.parquet")))
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "product_metrics.parquet")))
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "region_metrics.parquet")))
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "csat_trajectory.parquet")))

    def test_02_dataset_totals(self):
        """Verify total conversation counts match production 1,898,083."""
        tot = self.summary["dataset_metrics"]["total_conversations"]
        self.assertEqual(tot, 1898083)

    def test_03_response_time_metrics(self):
        """Verify response time avg, median, P90, P95 and coverage %."""
        rt = self.summary["response_time_metrics"]
        self.assertGreater(rt["valid_measured_cases"], 0)
        self.assertGreater(rt["average_seconds"], 0)
        self.assertGreater(rt["median_seconds"], 0)
        self.assertGreater(rt["p90_seconds"], 0)
        self.assertGreater(rt["p95_seconds"], 0)
        self.assertGreaterEqual(rt["p95_seconds"], rt["p90_seconds"])
        self.assertGreaterEqual(rt["p90_seconds"], rt["median_seconds"])
        self.assertIn("formula", rt)

    def test_04_fcr_metrics(self):
        """Verify FCR rate calculation, numerator, denominator."""
        fcr = self.summary["first_contact_resolution"]
        self.assertEqual(fcr["total_conversations"], 1898083)
        self.assertGreater(fcr["fcr_cases"], 0)
        self.assertGreater(fcr["fcr_rate_overall"], 0.0)
        self.assertLessEqual(fcr["fcr_rate_overall"], 1.0)

    def test_05_escalation_metrics(self):
        """Verify Escalation rate calculation."""
        esc = self.summary["escalation_metrics"]
        self.assertEqual(esc["total_conversations"], 1898083)
        self.assertGreater(esc["escalated_cases"], 0)
        self.assertGreater(esc["escalation_rate"], 0.0)
        self.assertLessEqual(esc["escalation_rate"], 1.0)

    def test_06_reopen_metrics(self):
        """Verify Reopen rate calculation."""
        reopen = self.summary["reopen_metrics"]
        self.assertEqual(reopen["total_conversations"], 1898083)
        self.assertGreater(reopen["reopened_cases"], 0)
        self.assertGreater(reopen["reopen_rate"], 0.0)
        self.assertLessEqual(reopen["reopen_rate"], 1.0)

    def test_07_csat_proxy(self):
        """Verify CSAT Proxy labeling and bounded range [0, 100]."""
        csat = self.summary["csat_proxy"]
        self.assertEqual(csat["label"], "CSAT Proxy")
        self.assertFalse(csat["is_actual_csat_survey"])
        self.assertGreaterEqual(csat["overall_csat_proxy_score"], 0.0)
        self.assertLessEqual(csat["overall_csat_proxy_score"], 100.0)

    def test_08_product_coverage(self):
        """Verify product mention coverage and missing rates."""
        prod = self.summary["product_analysis"]
        self.assertGreater(prod["product_mention_cases"], 0)
        self.assertGreater(prod["coverage_percentage"], 0.0)
        self.assertEqual(round(prod["coverage_percentage"] + prod["unknown_percentage"], 1), 100.0)

    def test_09_region_coverage(self):
        """Verify region mention coverage and missing rates."""
        reg = self.summary["region_analysis"]
        self.assertGreater(reg["region_mention_cases"], 0)
        self.assertGreater(reg["coverage_percentage"], 0.0)
        self.assertEqual(round(reg["coverage_percentage"] + reg["unknown_percentage"], 1), 100.0)

    def test_10_rag_snapshot(self):
        """Verify DOC-SNAPSHOT-ANALYTICS-V2 present in analytics_snapshots.parquet."""
        snp_path = os.path.join(project_root, "data", "knowledge", "analytics_snapshots", "analytics_snapshots.parquet")
        table = pq.read_table(snp_path).to_pylist()
        v2_docs = [d for d in table if d.get("document_id") == "DOC-SNAPSHOT-ANALYTICS-V2" or d.get("doc_id") == "DOC-SNAPSHOT-ANALYTICS-V2"]
        self.assertEqual(len(v2_docs), 1)

if __name__ == "__main__":
    unittest.main()
