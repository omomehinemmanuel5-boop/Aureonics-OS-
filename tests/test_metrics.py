import unittest

from app.services.governor_service import compute_alert
from app.services.metrics_service import compute_adv, compute_ccp, compute_iec


class TestAureonicsMetrics(unittest.TestCase):
    def test_ccp_decreases_under_perturbation(self):
        anchor = "Maintain continuity in constitutional governance across turns"
        stable = compute_ccp(anchor, [anchor, anchor, anchor], [1, 2, 3])
        perturbed = compute_ccp(anchor, ["random noise", "detached fragment", "unrelated output"], [1, 2, 3])
        self.assertGreater(stable["ccp"], perturbed["ccp"])

    def test_iec_decreases_with_inconsistent_ratios(self):
        consistent_pairs = [
            ("short input", "short output"),
            ("another brief input", "another brief output"),
            ("clear request", "clear response"),
        ]
        inconsistent_pairs = [
            ("tiny", "a very long output with many many tokens and extra expansion"),
            ("very long input with many many tokens and terms", "tiny"),
            ("medium input here", "extremely verbose output with unrelated details and drift"),
        ]
        iec_consistent = compute_iec(consistent_pairs)
        iec_inconsistent = compute_iec(inconsistent_pairs)
        self.assertGreater(iec_consistent["iec"], iec_inconsistent["iec"])

    def test_adv_decreases_under_constraint_violations(self):
        decisions = ["A", "B", "C", "A", "B", "C"]
        mostly_compliant = compute_adv(decisions, [True, True, True, True, True, False])
        violation_heavy = compute_adv(decisions, [False, False, True, False, False, True])
        self.assertGreater(mostly_compliant["adv"], violation_heavy["adv"])

    def test_margin_tracks_weakest_pillar(self):
        weakest, alert = compute_alert(0.82, 0.74, 0.11)
        self.assertEqual(weakest, "Sovereignty")
        self.assertIn("Sovereignty collapse", alert)


if __name__ == "__main__":
    unittest.main()
