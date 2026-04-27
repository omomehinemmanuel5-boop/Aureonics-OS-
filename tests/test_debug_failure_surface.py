from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_shape():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "kernel_ready" in data
