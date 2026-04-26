import json
import unittest
from pathlib import Path

from app.services.cbf_service import simulate_cbf


class TestFPL1Metrics(unittest.TestCase):
    def test_fpl1_metrics_and_report_export(self):
        result = simulate_cbf(steps=40, dt=0.05, seed=7, alpha=0.5, cbf_enabled=True, enforce_proof_assertions=False)
        self.assertIn("stability_ratio", result)
        self.assertIn("delta_v_positive_ratio", result)
        self.assertIn("max_deviation", result)
        self.assertIn("invariance_violations", result)
        self.assertIn("fpl1_classification", result)
        self.assertGreaterEqual(result["stability_ratio"], 0.0)
        self.assertLessEqual(result["stability_ratio"], 1.0)
        self.assertLess(result["max_deviation"], 0.25)
        self.assertEqual(result["invariance_violations"], 0)

        report_path = Path("logs/fpl1_report.json")
        self.assertTrue(report_path.exists())
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertIn("classification", payload)


if __name__ == "__main__":
    unittest.main()
