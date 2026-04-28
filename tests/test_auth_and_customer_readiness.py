from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_auth_register_login_and_me_contract():
    register = client.post(
        "/auth/register",
        json={
            "email": "pilot@example.com",
            "password": "S3curePassword!",
            "company_name": "Pilot Co",
        },
    )
    assert register.status_code == 200
    reg_data = register.json()
    assert reg_data["token_type"] == "bearer"
    assert reg_data["user"]["email"] == "pilot@example.com"

    token = reg_data["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    me_data = me.json()
    assert me_data["email"] == "pilot@example.com"
    assert me_data["company_name"] == "Pilot Co"

    login = client.post(
        "/auth/login",
        json={
            "email": "pilot@example.com",
            "password": "S3curePassword!",
        },
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_paid_plan_and_checkout_work_without_authentication():
    paid_without_auth = client.post(
        "/lex/run",
        headers={"x-subscription-plan": "pro"},
        json={"prompt": "Explain policy drift.", "firewall_mode": True},
    )
    assert paid_without_auth.status_code == 200
    assert paid_without_auth.json()["plan"] == "pro"

    checkout = client.post(
        "/billing/checkout",
        json={
            "plan": "pro",
            "buyer_email": "buyer@example.com",
            "company_name": "Buyer Co",
            "seats": 3,
        },
    )
    assert checkout.status_code == 200
    assert checkout.json()["amount_usd"] == 57
