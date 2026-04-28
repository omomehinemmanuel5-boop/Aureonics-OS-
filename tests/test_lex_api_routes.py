from fastapi.testclient import TestClient

from app.main import app


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
    }
    assert expected.issubset(data.keys())


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
    assert checkout["amount_usd"] == 57
    assert checkout["payment_terms_days"] == 14
    assert checkout["wire_reference"].startswith("LEX-PRO-")
    assert len(checkout["payment_instructions"]) >= 2
