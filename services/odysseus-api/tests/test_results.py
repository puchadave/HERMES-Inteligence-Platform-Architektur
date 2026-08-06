import json
import uuid
from pathlib import Path

import pytest

from app.results import ResultNotFoundError, ResultStore


def create_job(root: Path, *, complete: bool = True) -> str:
    job_id = str(uuid.uuid4())
    directory = root / job_id
    directory.mkdir()
    if complete:
        (directory / "result.json").write_text(json.dumps({"job_id": job_id, "target": "example.org"}), encoding="utf-8")
        (directory / "summary.md").write_text(f"# {job_id}\n", encoding="utf-8")
    return job_id


def test_reads_result_and_report(tmp_path: Path) -> None:
    job_id = create_job(tmp_path)
    store = ResultStore(tmp_path)

    assert store.get_result(job_id)["target"] == "example.org"
    assert store.get_report(job_id) == f"# {job_id}\n"


def test_lists_completed_and_processing_jobs(tmp_path: Path) -> None:
    complete = create_job(tmp_path, complete=True)
    processing = create_job(tmp_path, complete=False)
    store = ResultStore(tmp_path)

    by_id = {entry["job_id"]: entry for entry in store.list_results()}
    assert by_id[complete]["status"] == "completed"
    assert by_id[processing]["status"] == "processing"


def test_rejects_path_traversal_and_unknown_job(tmp_path: Path) -> None:
    store = ResultStore(tmp_path)
    with pytest.raises(ResultNotFoundError):
        store.get_result("../../etc/passwd")
    with pytest.raises(ResultNotFoundError):
        store.get_result(str(uuid.uuid4()))
