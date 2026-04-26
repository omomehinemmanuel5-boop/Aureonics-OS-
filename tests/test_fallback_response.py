from fastapi.testclient import TestClient

from app.main import app, kernel


def test_lex_run_returns_fallback_on_llm_failure():
    original_run_cycle = kernel.run_cycle

    try:
        kernel.run_cycle = lambda *_args, **_kwargs: {"status": "Error", "reason": "simulated llm failure"}
        client = TestClient(app)
        response = client.post("/lex/run", json={"prompt": "Hello"})

        assert response.status_code == 200
        payload = response.json()
        assert "fallback" in payload["final_output"].lower()
        assert payload["intervention"] is True
    finally:
        kernel.run_cycle = original_run_cycle
