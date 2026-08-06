import json
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.results import ResultStore

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


def test_job_result_endpoints(tmp_path: Path, monkeypatch) -> None:
    job_id = str(uuid.uuid4())
    directory = tmp_path / job_id
    directory.mkdir()
    (directory / "result.json").write_text(json.dumps({"job_id": job_id, "target": "example.org"}), encoding="utf-8")
    (directory / "summary.md").write_text("# Report\n", encoding="utf-8")
    monkeypatch.setattr("app.main.get_result_store", lambda: ResultStore(tmp_path))

    listing = client.get("/v1/jobs")
    result = client.get(f"/v1/jobs/{job_id}")
    report = client.get(f"/v1/jobs/{job_id}/report")

    assert listing.status_code == 200
    assert listing.json()["jobs"][0]["job_id"] == job_id
    assert result.json()["target"] == "example.org"
    assert report.headers["content-type"].startswith("text/markdown")
    assert report.text == "# Report\n"


def test_unknown_job_returns_404(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_result_store", lambda: ResultStore(tmp_path))
    response = client.get(f"/v1/jobs/{uuid.uuid4()}")
    assert response.status_code == 404
