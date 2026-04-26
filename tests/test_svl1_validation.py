import unittest

from svl_validation import run_svl1_validation


class TestSVL1Validation(unittest.TestCase):
    def test_svl1_rejects_non_positive_run_count(self):
        with self.assertRaises(ValueError):
            run_svl1_validation(num_runs=0, enforce_assertions=False)


if __name__ == "__main__":
    unittest.main()
