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

    def test_parameter_sweep_combinations(self):
        sweep = parameter_sweep(steps=12, dt=0.05, tau=THRESHOLD, seed=3)
        expected_pairs = 3 * 4
        self.assertEqual(len(sweep), expected_pairs)
        self.assertTrue(all("alpha" in row and "k" in row for row in sweep))


if __name__ == "__main__":
    unittest.main()
