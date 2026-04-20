import unittest

from app.services.governor_service import THRESHOLD, compute_alert, governor_state


class TestGovernorLogic(unittest.TestCase):
    def test_governor_triggers_on_any_pillar_below_tau(self):
        state = governor_state(0.91, 0.59, 0.93, tau=0.6)
        self.assertTrue(state["active"])
        self.assertEqual(state["violated_pillars"], ["Reciprocity"])
        self.assertEqual(state["weakest_pillar"], "Reciprocity")
        self.assertGreater(state["governance_pressure"], 0.0)

    def test_default_threshold_updated(self):
        self.assertEqual(THRESHOLD, 0.15)

    def test_governor_inactive_when_all_above_tau(self):
        state = governor_state(0.71, 0.64, 0.66, tau=0.6)
        self.assertFalse(state["active"])
        self.assertEqual(state["violated_pillars"], [])
        self.assertIn(state["constitutional_band"], {"watch", "stable-core"})

    def test_corrections_include_expected_fields(self):
        state = governor_state(0.08, 0.41, 0.52, tau=0.15)
        self.assertEqual(state["violated_pillars"], ["Continuity"])
        correction = state["corrections"][0]
        self.assertIn("action", correction)
        self.assertIn("expected_shift", correction)
        self.assertEqual(correction["target_mode"], "Analytical")

    def test_alert_text_reflects_band(self):
        weakest, alert = compute_alert(0.06, 0.42, 0.53)
        self.assertEqual(weakest, "Continuity")
        self.assertIn("collapse-risk", alert)


if __name__ == "__main__":
    unittest.main()
