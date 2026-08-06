from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_classify_endpoint() -> None:
    response = client.post("/v1/classify", json={"query": "domain metadata", "profile": "domains"})
    assert response.status_code == 200
    assert response.json()["route"] == "xeon_queue"


def test_metrics() -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "odysseus_api_up 1" in response.text
