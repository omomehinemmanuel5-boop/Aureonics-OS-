import uuid
from fastapi.testclient import TestClient

from app.main import app, create_app
from app.database import SessionLocal
from app.models.entities import AuditLedgerEntry, UsageLog


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
    demo_identity = f"198.51.100.{uuid.uuid4().int % 200 + 1}"
    demo_resp = client.get("/demo", headers={"x-forwarded-for": demo_identity, "x-subscription-plan": "enterprise"})
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
    identity = f"203.0.113.{uuid.uuid4().int % 200 + 1}"
    headers = {"x-forwarded-for": identity}
    with SessionLocal() as db:
        db.query(UsageLog).filter(UsageLog.user_id == identity).delete()
        db.commit()
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


def test_trust_receipt_retrieval_and_signature_verification_flow():
    run_resp = client.post("/lex/run", json={"prompt": "Create a balanced policy summary."})
    assert run_resp.status_code == 200
    run = run_resp.json()

    created = client.post(
        "/lex/trust-receipt",
        json={"prompt": "Create a balanced policy summary.", "response": run, "run_id": "run_verify_001"},
    )
    assert created.status_code == 200
    receipt = created.json()

    fetched = client.get("/lex/trust-receipt/run_verify_001")
    assert fetched.status_code == 200
    assert fetched.json()["run_id"] == "run_verify_001"

    valid_check = client.post("/lex/trust-receipt/verify", json={"receipt": receipt})
    assert valid_check.status_code == 200
    assert valid_check.json()["valid"] is True
    assert valid_check.json()["reason"] == "Signature valid"

    tampered = dict(receipt)
    tampered["final_output_hash"] = "0" * 64
    invalid_check = client.post("/lex/trust-receipt/verify", json={"receipt": tampered})
    assert invalid_check.status_code == 200
    assert invalid_check.json()["valid"] is False
    assert invalid_check.json()["reason"] == "Signature mismatch"


def test_sales_bridge_stability_bounds_and_sovereignty_badge():
    run_headers = {"x-forwarded-for": f"198.51.100.{uuid.uuid4().int % 200 + 1}"}
    run_headers["x-subscription-plan"] = "enterprise"
    run_resp = client.post("/lex/run", headers=run_headers, json={"prompt": "Draft lawful procurement response."})
    assert run_resp.status_code == 200
    run = run_resp.json()

    receipt_resp = client.post(
        "/lex/trust-receipt",
        json={"prompt": "Draft lawful procurement response.", "response": run, "run_id": "run_audit_001"},
    )
    assert receipt_resp.status_code == 200

    sales = client.post(
        "/lex/sales-bridge",
        json={"run_id": "run_audit_001", "company_name": "Acme Bank", "buyer_role": "Chief Risk Officer"},
    )
    assert sales.status_code == 200
    sales_body = sales.json()
    assert sales_body["risk_band"] in {"green", "amber", "red"}
    assert sales_body["recommended_plan"] in {"pro", "enterprise"}
    assert sales_body["confidence_score"] >= 0

    bounds = client.get("/lex/stability-bounds")
    assert bounds.status_code == 200
    bounds_body = bounds.json()
    assert bounds_body["window_size"] >= 1
    assert 0 <= bounds_body["lower_bound"] <= 1

    badge = client.get("/lex/trust-receipt/run_audit_001/badge")
    assert badge.status_code == 200
    badge_body = badge.json()
    assert "<svg" in badge_body["badge_svg"]
    assert badge_body["run_id"] == "run_audit_001"

    export = client.get("/lex/trust-receipt/run_audit_001/export")
    assert export.status_code == 200
    export_body = export.json()
    assert export_body["signed_export"]["badge_hash"] == export_body["badge_hash"]
    assert len(export_body["export_hash"]) == 64
    assert len(export_body["ledger_chain_hash"]) == 64

    chain = client.get("/lex/audit-ledger/verify")
    assert chain.status_code == 200
    assert chain.json()["valid"] is True

    with SessionLocal() as db:
        row = db.get(AuditLedgerEntry, "run_audit_001")
        assert row is not None
        row.tier = "tamper-attempt"
        try:
            db.commit()
            assert False, "commit should fail for immutable audit ledger"
        except Exception:
            db.rollback()
