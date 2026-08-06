from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any


class ResultNotFoundError(FileNotFoundError):
    pass


class ResultStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    @staticmethod
    def validate_job_id(job_id: str) -> str:
        try:
            return str(uuid.UUID(job_id))
        except ValueError as exc:
            raise ResultNotFoundError(job_id) from exc

    def _job_dir(self, job_id: str) -> Path:
        return self.root / self.validate_job_id(job_id)

    def get_result(self, job_id: str) -> dict[str, Any]:
        path = self._job_dir(job_id) / "result.json"
        if not path.is_file():
            raise ResultNotFoundError(job_id)
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"Invalid result document for {job_id}")
        return value

    def get_report(self, job_id: str) -> str:
        path = self._job_dir(job_id) / "summary.md"
        if not path.is_file():
            raise ResultNotFoundError(job_id)
        return path.read_text(encoding="utf-8")

    def list_results(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []
        entries: list[dict[str, Any]] = []
        directories = sorted(
            (path for path in self.root.iterdir() if path.is_dir()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for directory in directories[:limit]:
            try:
                job_id = self.validate_job_id(directory.name)
            except ResultNotFoundError:
                continue
            result_path = directory / "result.json"
            entries.append(
                {
                    "job_id": job_id,
                    "status": "completed" if result_path.is_file() else "processing",
                    "updated_at": directory.stat().st_mtime,
                }
            )
        return entries
