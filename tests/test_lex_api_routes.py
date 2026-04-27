from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_post_trace_returns_canonical_shape():
    payload = {"prompt": "Explain policy drift.", "firewall_mode": True}
    response = client.post("/api/lex/trace", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert {"id", "createdAt", "prompt", "raw", "governed", "final", "reason", "metrics"}.issubset(data.keys())
    assert {"M", "C", "R", "S", "ADV", "semanticDiff", "intervened", "health"}.issubset(
        data["metrics"].keys()
    )


def test_trace_metrics_audit_and_policies_routes():
    create_resp = client.post("/api/lex/trace", json={"prompt": "safe prompt"})
    trace_id = create_resp.json()["id"]

    trace_resp = client.get(f"/api/lex/trace/{trace_id}")
    metrics_resp = client.get("/api/lex/metrics")
    audit_resp = client.get("/api/lex/audit")
    policies_resp = client.get("/api/lex/policies")

    assert trace_resp.status_code == 200
    assert metrics_resp.status_code == 200
    assert audit_resp.status_code == 200
    assert policies_resp.status_code == 200

    metrics = metrics_resp.json()
    assert {"M", "ADV", "interventionsToday", "health"}.issubset(metrics.keys())

    audit = audit_resp.json()
    assert {"count", "items"}.issubset(audit.keys())

    policies = policies_resp.json()
    assert isinstance(policies, list)
    assert len(policies) >= 1
