from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

from app.reporting import write_report


def test_report_persists_canonical_result_and_valid_hashes(tmp_path: Path) -> None:
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "query": "example.org",
        "profile": "domain_infrastructure",
        "requested_by": "pytest",
    }
    result = {
        "job_id": job_id,
        "target": "example.org",
        "target_kind": "domain",
        "started_at": "2026-08-06T00:00:00+00:00",
        "finished_at": "2026-08-06T00:00:01+00:00",
        "tools": [
            {
                "name": "search_dns",
                "status": "ok",
                "duration_ms": 12,
                "arguments": {"domain": "example.org", "json_output": True},
                "result": {"records": []},
            }
        ],
        "bbot": {"status": "disabled"},
        "github_mcp": None,
    }

    artifacts = write_report(str(tmp_path), job, result)
    persisted = json.loads(Path(artifacts["json"]).read_text(encoding="utf-8"))

    assert persisted["artifacts"] == artifacts
    assert persisted["target"] == "example.org"
    assert "# Odysseus Research Report" in Path(artifacts["markdown"]).read_text(encoding="utf-8")

    manifest_entries = {}
    for line in Path(artifacts["manifest"]).read_text(encoding="utf-8").splitlines():
        digest, filename = line.split("  ", 1)
        manifest_entries[filename] = digest

    for filename in ("result.json", "summary.md"):
        path = Path(artifacts["directory"]) / filename
        assert manifest_entries[filename] == hashlib.sha256(path.read_bytes()).hexdigest()
