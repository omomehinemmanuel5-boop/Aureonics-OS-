import unittest

from app.services.governor_service import THRESHOLD, governor_state


class TestGovernorLogic(unittest.TestCase):
    def test_governor_triggers_on_any_pillar_below_tau(self):
        state = governor_state(0.91, 0.59, 0.93, tau=0.6)
        self.assertTrue(state["active"])
        self.assertEqual(state["violated_pillars"], ["Reciprocity"])


    def test_default_threshold_updated(self):
        self.assertEqual(THRESHOLD, 0.15)

    def test_governor_inactive_when_all_above_tau(self):
        state = governor_state(0.71, 0.64, 0.66, tau=0.6)
        self.assertFalse(state["active"])
        self.assertEqual(state["violated_pillars"], [])


if __name__ == "__main__":
    unittest.main()
