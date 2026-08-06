from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import nats

from .mcp_client import MCPClient
from .planner import TargetKind, build_plan, classify_target, extract_target, normalize_target
from .reporting import normalize_tool_result, utc_now, write_report
from .source_intelligence import collect_repository_context

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("odysseus-osint-worker")

NATS_URL = os.getenv("ODYSSEUS_NATS_URL", "nats://localhost:4222")
NATS_SUBJECT = os.getenv("ODYSSEUS_NATS_SUBJECT", "odysseus.jobs.search")
NATS_RESULT_SUBJECT = os.getenv("ODYSSEUS_NATS_RESULT_SUBJECT", "odysseus.results.search")
OPENOSINT_MCP_URL = os.getenv("OPENOSINT_MCP_URL", "http://openosint-mcp:8000/mcp")
GITHUB_MCP_URL = os.getenv("GITHUB_MCP_URL", "http://github-mcp:8082/mcp")
GITHUB_MCP_TOKEN = os.getenv("GITHUB_MCP_TOKEN", "")
REPORT_DIR = os.getenv("ODYSSEUS_REPORT_DIR", "/data/jobs")
MAX_PARALLEL_TOOLS = max(1, int(os.getenv("ODYSSEUS_MAX_PARALLEL_TOOLS", "3")))
INCLUDE_PAID = os.getenv("ODYSSEUS_ENABLE_PAID_OSINT", "false").lower() == "true"
ENABLE_BBOT = os.getenv("ODYSSEUS_ENABLE_BBOT", "false").lower() == "true"
BBOT_TIMEOUT_SECONDS = int(os.getenv("ODYSSEUS_BBOT_TIMEOUT_SECONDS", "900"))


def secret_is_available(name: str | None) -> bool:
    return name is None or bool(os.getenv(name))


async def run_bbot_passive(domain: str, job_dir: Path) -> dict[str, Any]:
    if not ENABLE_BBOT:
        return {"status": "disabled"}

    def scan() -> dict[str, Any]:
        from bbot.scanner import Preset, Scanner

        scan_name = f"{domain.replace('.', '-')}-passive"
        output_dir = job_dir / "bbot"
        output_dir.mkdir(parents=True, exist_ok=True)
        preset = Preset(
            domain,
            flags=["safe", "subdomain-enum", "affiliates", "email-enum", "social-enum"],
            require_flags=["passive"],
            scan_name=scan_name,
            silent=True,
            output_dir=str(output_dir),
        )
        scanner = Scanner(preset=preset)
        counts: dict[str, int] = {}
        samples: dict[str, list[str]] = {}
        for event in scanner.start():
            event_type = str(getattr(event, "type", "UNKNOWN"))
            counts[event_type] = counts.get(event_type, 0) + 1
            bucket = samples.setdefault(event_type, [])
            if len(bucket) < 25:
                bucket.append(str(getattr(event, "data", event)))
        return {
            "status": "completed",
            "scan_name": scanner.name,
            "home": str(scanner.home),
            "counts": counts,
            "samples": samples,
        }

    try:
        return await asyncio.wait_for(asyncio.to_thread(scan), timeout=BBOT_TIMEOUT_SECONDS)
    except TimeoutError:
        return {"status": "timeout", "timeout_seconds": BBOT_TIMEOUT_SECONDS}
    except Exception as exc:  # BBOT modules fail independently; preserve the MCP results.
        logger.exception("BBOT scan failed for %s", domain)
        return {"status": "error", "error": str(exc)}


async def execute_tool(
    client: MCPClient,
    available_tools: set[str],
    call: Any,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    record: dict[str, Any] = {"name": call.name, "arguments": call.arguments}
    if call.name not in available_tools:
        return {**record, "status": "unavailable", "duration_ms": 0, "error": "Tool not exposed by MCP server"}
    if not secret_is_available(call.optional_secret):
        return {
            **record,
            "status": "skipped",
            "duration_ms": 0,
            "error": f"Missing optional secret: {call.optional_secret}",
        }

    started = time.perf_counter()
    async with semaphore:
        try:
            raw = await client.call_tool(call.name, call.arguments)
            return {
                **record,
                "status": "ok",
                "duration_ms": round((time.perf_counter() - started) * 1000),
                "result": normalize_tool_result(raw),
            }
        except Exception as exc:
            logger.exception("MCP tool %s failed", call.name)
            return {
                **record,
                "status": "error",
                "duration_ms": round((time.perf_counter() - started) * 1000),
                "error": str(exc),
            }


async def process_job(job: dict[str, Any]) -> dict[str, Any]:
    started_at = utc_now()
    metadata = job.get("metadata") if isinstance(job.get("metadata"), dict) else {}
    query = str(job.get("query", ""))
    target = str(metadata.get("target") or extract_target(query))
    kind = classify_target(target)
    target = normalize_target(target, kind)
    plan = build_plan(target, include_paid=INCLUDE_PAID)
    semaphore = asyncio.Semaphore(MAX_PARALLEL_TOOLS)

    async with MCPClient(OPENOSINT_MCP_URL) as client:
        tool_descriptors = await client.list_tools()
        available_tools = {str(tool.get("name")) for tool in tool_descriptors if tool.get("name")}
        tasks = [execute_tool(client, available_tools, call, semaphore) for call in plan]
        tool_results = await asyncio.gather(*tasks)

    job_dir = Path(REPORT_DIR) / str(job["job_id"])
    bbot_result: dict[str, Any] | None = None
    if kind is TargetKind.DOMAIN:
        bbot_result = await run_bbot_passive(target, job_dir)

    github_context: dict[str, Any] | None = None
    try:
        github_context = await collect_repository_context(
            f"{query} {target}",
            mcp_url=GITHUB_MCP_URL,
            token=GITHUB_MCP_TOKEN,
        )
    except Exception as exc:
        logger.exception("GitHub MCP enrichment failed")
        github_context = {"status": "error", "error": str(exc)}

    result = {
        "schema_version": "1.0",
        "job_id": job["job_id"],
        "target": target,
        "target_kind": kind.value,
        "profile": job.get("profile", "specialist"),
        "requested_by": job.get("requested_by", "unknown"),
        "started_at": started_at,
        "finished_at": utc_now(),
        "tools": tool_results,
        "bbot": bbot_result,
        "github_mcp": github_context,
    }
    result["artifacts"] = write_report(REPORT_DIR, job, result)
    return result


async def run() -> None:
    nc = await nats.connect(NATS_URL, name="odysseus-osint-worker", reconnect_time_wait=2, max_reconnect_attempts=-1)
    logger.info("Connected to NATS; waiting on %s", NATS_SUBJECT)

    async def callback(message: Any) -> None:
        try:
            job = json.loads(message.data.decode("utf-8"))
            if not isinstance(job, dict) or "job_id" not in job:
                raise ValueError("Invalid Odysseus job payload")
            logger.info("Processing job %s", job["job_id"])
            result = await process_job(job)
            await nc.publish(NATS_RESULT_SUBJECT, json.dumps(result, ensure_ascii=False).encode("utf-8"))
            await nc.flush()
            logger.info("Finished job %s", job["job_id"])
        except Exception:
            logger.exception("Research job failed")

    await nc.subscribe(NATS_SUBJECT, queue="odysseus-osint-workers", cb=callback)
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await nc.drain()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
