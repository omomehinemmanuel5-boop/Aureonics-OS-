from fastapi.testclient import TestClient

from app.main import app


def test_root_loads_successfully():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "Lex Aureon" in response.text


def test_dashboard_loads_successfully():
    client = TestClient(app)
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Lex Aureon" in response.text
