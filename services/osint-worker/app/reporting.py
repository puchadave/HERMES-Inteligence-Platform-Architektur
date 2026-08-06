from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def normalize_tool_result(result: dict[str, Any]) -> Any:
    content = result.get("content")
    if not isinstance(content, list):
        return result

    values: list[Any] = []
    for item in content:
        if not isinstance(item, dict):
            values.append(item)
            continue
        text = item.get("text")
        if not isinstance(text, str):
            values.append(item)
            continue
        try:
            values.append(json.loads(text))
        except json.JSONDecodeError:
            values.append(text)
    if len(values) == 1:
        return values[0]
    return values


def write_report(base_dir: str, job: dict[str, Any], result: dict[str, Any]) -> dict[str, str]:
    job_id = str(job["job_id"])
    directory = Path(base_dir) / job_id
    directory.mkdir(parents=True, exist_ok=True)

    json_path = directory / "result.json"
    markdown_path = directory / "summary.md"
    manifest_path = directory / "manifest.sha256"

    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    json_path.write_bytes(encoded)

    lines = [
        f"# Odysseus Research Report · {job_id}",
        "",
        f"- Query: `{job.get('query', '')}`",
        f"- Profile: `{job.get('profile', '')}`",
        f"- Requested by: `{job.get('requested_by', 'unknown')}`",
        f"- Target: `{result.get('target', '')}`",
        f"- Target type: `{result.get('target_kind', '')}`",
        f"- Started: `{result.get('started_at', '')}`",
        f"- Finished: `{result.get('finished_at', '')}`",
        "",
        "## Tool results",
        "",
    ]
    for item in result.get("tools", []):
        lines.extend(
            [
                f"### {item.get('name', 'unknown')}",
                f"- Status: `{item.get('status', 'unknown')}`",
                f"- Duration: `{item.get('duration_ms', 0)} ms`",
                f"- Arguments: `{json.dumps(item.get('arguments', {}), ensure_ascii=False, sort_keys=True)}`",
                "",
            ]
        )
        if item.get("error"):
            lines.extend([f"Error: `{item['error']}`", ""])
        else:
            lines.extend(
                [
                    "```json",
                    json.dumps(item.get("result"), ensure_ascii=False, indent=2, sort_keys=True),
                    "```",
                    "",
                ]
            )

    if result.get("bbot"):
        lines.extend(["## BBOT passive scan", "", "```json", json.dumps(result["bbot"], ensure_ascii=False, indent=2, sort_keys=True), "```", ""])

    markdown_path.write_text("\n".join(lines), encoding="utf-8")

    manifest_lines = []
    for path in (json_path, markdown_path):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_lines.append(f"{digest}  {path.name}")
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    return {
        "directory": str(directory),
        "json": str(json_path),
        "markdown": str(markdown_path),
        "manifest": str(manifest_path),
    }
