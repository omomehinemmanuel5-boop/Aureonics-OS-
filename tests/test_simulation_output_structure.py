import json
import unittest


class TestSimulationOutputStructure(unittest.TestCase):
    def test_simplex_normalized_in_synthetic_output(self):
        with open("simulation_output.json", "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertEqual(payload["tau_configured"], 0.15)
        self.assertGreaterEqual(payload["tau_empirical"], 0.0)

        for step in payload["trajectory"]:
            pre = step["pre_correction"]
            post = step["post_correction"]
            self.assertAlmostEqual(pre["C"] + pre["R"] + pre["S"], 1.0, places=3)
            self.assertAlmostEqual(post["C"] + post["R"] + post["S"], 1.0, places=3)

    def test_basin_transitions_present(self):
        with open("simulation_output.json", "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertGreater(len(payload["basin_transitions"]), 0)


if __name__ == "__main__":
    unittest.main()
