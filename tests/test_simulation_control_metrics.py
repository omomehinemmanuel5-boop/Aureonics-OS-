import unittest

from app.services.governor_service import THRESHOLD
from app.services.simulation_service import parameter_sweep, simulate_mode


class TestSimulationControlMetrics(unittest.TestCase):
    def test_measurement_fields_exist(self):
        result = simulate_mode(
            steps=20,
            governor_enabled=True,
            tau=THRESHOLD,
            dt=0.05,
            alpha=0.5,
            k=2.0,
            seed=7,
        )
        self.assertIn("time_below_tau", result)
        self.assertIn("recovery_times", result)
        self.assertIn("violations", result)
        self.assertIn("collapse_detected", result)
        self.assertIn("near_collapse_count", result)
        self.assertIn("mean_C", result)
        self.assertIn("mean_R", result)
        self.assertIn("mean_S", result)

    def test_parameter_sweep_combinations(self):
        sweep = parameter_sweep(steps=12, dt=0.05, tau=THRESHOLD, seed=3)
        expected_pairs = 3 * 4
        self.assertEqual(len(sweep), expected_pairs)
        self.assertTrue(all("alpha" in row and "k" in row for row in sweep))
        expected_k_values = {2.0, 5.0, 10.0, 20.0}
        self.assertEqual({row["k"] for row in sweep}, expected_k_values)

    def test_symmetry_mode_preserves_balance_without_noise(self):
        result = simulate_mode(
            steps=40,
            governor_enabled=False,
            tau=THRESHOLD,
            dt=0.05,
            alpha=0.5,
            k=2.0,
            seed=7,
            symmetry_test=True,
        )
        self.assertAlmostEqual(result["mean_C"], result["mean_R"], places=6)
        self.assertAlmostEqual(result["mean_R"], result["mean_S"], places=6)


if __name__ == "__main__":
    unittest.main()
