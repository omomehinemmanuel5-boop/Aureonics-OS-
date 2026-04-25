import unittest

from fastapi.testclient import TestClient

from app.main import app, kernel
from sovereign_kernel_v2 import SovereignKernel


class TestSovereignKernel(unittest.TestCase):
    def test_kernel_initializes_with_valid_simplex(self):
        sk = SovereignKernel()
        total = sk.state["C"] + sk.state["R"] + sk.state["S"]
        self.assertAlmostEqual(total, 1.0, places=6)
        self.assertGreaterEqual(min(sk.state.values()), sk.tau)

    def test_projection_enforces_floor_and_simplex(self):
        sk = SovereignKernel()
        sk.state = {"C": -0.20, "R": 0.10, "S": 1.10}
        projected = sk.project_to_simplex()

        self.assertTrue(projected)
        total = sk.state["C"] + sk.state["R"] + sk.state["S"]
        self.assertAlmostEqual(total, 1.0, places=6)
        self.assertGreaterEqual(min(sk.state.values()), sk.tau)

    def test_praxis_run_endpoint_executes(self):
        original_call_llm = kernel.call_llm
        original_state = dict(kernel.state)

        try:
            kernel.call_llm = lambda prompt: "Constitutional response with autonomous variance and stable exchange."
            client = TestClient(app)
            response = client.post("/praxis/run", json={"prompt": "Refine this agreement respectfully."})
            self.assertEqual(response.status_code, 200)

            payload = response.json()
            self.assertEqual(payload["status"], "Success")
            state = payload["state"]
            total = state["C"] + state["R"] + state["S"]
            self.assertAlmostEqual(total, 1.0, places=6)
            self.assertGreaterEqual(min(state.values()), kernel.tau)
            self.assertIn("receipt", payload)
        finally:
            kernel.call_llm = original_call_llm
            kernel.state = original_state


if __name__ == "__main__":
    unittest.main()
