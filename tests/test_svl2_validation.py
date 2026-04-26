import os
import unittest
from unittest.mock import patch

from sovereign_kernel_v2 import DEFAULT_MODEL, SovereignKernel
from svl_validation import run_svl2_cross_model_validation


class TestSVL2Validation(unittest.TestCase):
    def test_kernel_accepts_model_name_and_defaults(self):
        default_kernel = SovereignKernel()
        explicit_kernel = SovereignKernel(model_name="gpt-4o-mini")

        self.assertEqual(default_kernel.model_name, DEFAULT_MODEL)
        self.assertEqual(explicit_kernel.model_name, "gpt-4o-mini")

    @patch("svl_validation.run_svl1_validation")
    def test_svl2_allows_partial_run_when_only_one_key_available(self, mock_svl1):
        mock_svl1.return_value = {
            "summary": {
                "mean_M_avg": 0.2,
                "mean_M_std": 0.01,
                "failure_rate": 0.0,
                "projection_density_avg": 0.25,
                "pre_projection_violation_rate": 0.02,
            }
        }
        old_groq = os.environ.get("GROQ_API_KEY")
        old_openai = os.environ.pop("OPENAI_API_KEY", None)
        os.environ["GROQ_API_KEY"] = "test-key"
        try:
            report = run_svl2_cross_model_validation(num_runs=2, enforce_assertions=False)
        finally:
            if old_groq is not None:
                os.environ["GROQ_API_KEY"] = old_groq
            else:
                os.environ.pop("GROQ_API_KEY", None)
            if old_openai is not None:
                os.environ["OPENAI_API_KEY"] = old_openai
            else:
                os.environ.pop("OPENAI_API_KEY", None)

        self.assertEqual(report["executed_models"], ["groq-llama"])
        self.assertEqual(len(report["skipped_models"]), 1)
        self.assertIn("openai-gpt4o-mini", report["skipped_models"][0]["name"])
        self.assertIn("status", report)


if __name__ == "__main__":
    unittest.main()
