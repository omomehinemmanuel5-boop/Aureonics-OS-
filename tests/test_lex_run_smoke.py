from fastapi.testclient import TestClient

from app.main import app, kernel


def test_lex_run_smoke_minimal_payload():
    original_call_llm = kernel.call_llm
    original_state = dict(kernel.state)

    try:
        kernel.call_llm = lambda *_args, **_kwargs: "Stable model output for smoke test."
        client = TestClient(app)
        response = client.post("/lex/run", json={"prompt": "Hello"})

        assert response.status_code == 200
        payload = response.json()
        assert "raw_output" in payload
        assert "governed_output" in payload
        assert "final_output" in payload
        assert "intervention" in payload
        assert "M" in payload
    finally:
        kernel.call_llm = original_call_llm
        kernel.state = original_state
