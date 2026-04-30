from fastapi.testclient import TestClient

from app.main import app, create_app


client = TestClient(app)


def test_lex_run_contract_shape():
    response = client.post("/lex/run", json={"prompt": "Explain policy drift.", "firewall_mode": True})
    assert response.status_code == 200

    data = response.json()
    expected = {
        "raw_output",
        "governed_output",
        "final_output",
        "intervention",
        "intervention_reason",
        "semantic_diff_score",
        "M",
        "diff",
    }
    assert expected.issubset(data.keys())
    assert isinstance(data["diff"], list)
    assert all({"type", "text"}.issubset(chunk.keys()) for chunk in data["diff"])


def test_health_pricing_demo_and_checkout_stub():
    health_resp = client.get("/health")
    pricing_resp = client.get("/pricing")
    demo_resp = client.get("/demo")
    checkout_resp = client.post(
        "/billing/checkout",
        json={
            "plan": "pro",
            "buyer_email": "buyer@example.com",
            "company_name": "Acme Corp",
            "seats": 3,
        },
    )

    assert health_resp.status_code == 200
    assert pricing_resp.status_code == 200
    assert demo_resp.status_code == 200
    assert checkout_resp.status_code == 200

    pricing = pricing_resp.json()
    assert pricing.get("product")
    assert isinstance(pricing.get("plans"), list)

    demo = demo_resp.json()
    assert demo["intervention"] is True

    checkout = checkout_resp.json()
    assert checkout["checkout_mode"] == "manual_invoice"


def test_free_plan_daily_limit_and_upgrade_signal():
    headers = {"x-forwarded-for": "203.0.113.101"}
    for _ in range(10):
        ok = client.post("/lex/run", headers=headers, json={"prompt": "Summarize contract terms."})
        assert ok.status_code == 200
        body = ok.json()
        assert body.get("upgrade_required") is False

    blocked = client.post("/lex/run", headers=headers, json={"prompt": "11th request"})
    assert blocked.status_code == 200
    data = blocked.json()
    assert data["error"] == "LIMIT_REACHED"
    assert data["upgrade_required"] is True
    assert data["message"] == "You’ve used all 10 free runs today."
    assert data["final_output"] == ""


def test_trust_receipt_export_contains_hashes_and_signature():
    run_resp = client.post("/lex/run", json={"prompt": "Draft a compliant vendor onboarding checklist."})
    assert run_resp.status_code == 200
    run = run_resp.json()

    receipt_resp = client.post(
        "/lex/trust-receipt",
        json={
            "prompt": "Draft a compliant vendor onboarding checklist.",
            "response": run,
            "run_id": "run_demo_001",
        },
    )
    assert receipt_resp.status_code == 200
    receipt = receipt_resp.json()

    assert receipt["run_id"] == "run_demo_001"
    assert receipt["receipt_version"] == "1.0"
    assert len(receipt["input_hash"]) == 64
    assert len(receipt["raw_output_hash"]) == 64
    assert len(receipt["governed_output_hash"]) == 64
    assert len(receipt["final_output_hash"]) == 64
    assert len(receipt["integrity_signature"]) == 64
    assert isinstance(receipt["stability_timeline"], list)
    assert [step["stage"] for step in receipt["stability_timeline"]] == ["raw", "governed", "final"]


def test_landing_and_dashboard_redirect_to_frontend_when_configured(monkeypatch):
    monkeypatch.setenv("LEX_FRONTEND_BASE_URL", "https://ui.aureonics.ai")
    configured_client = TestClient(create_app())

    landing = configured_client.get("/", follow_redirects=False)
    dashboard = configured_client.get("/dashboard", follow_redirects=False)

    assert landing.status_code == 307
    assert landing.headers["location"] == "https://ui.aureonics.ai/"
    assert dashboard.status_code == 307
    assert dashboard.headers["location"] == "https://ui.aureonics.ai/app"
