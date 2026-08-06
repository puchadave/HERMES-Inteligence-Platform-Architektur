from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

import nats
import yaml

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("odysseus-osint-scheduler")

NATS_URL = os.getenv("ODYSSEUS_NATS_URL", "nats://localhost:4222")
NATS_SUBJECT = os.getenv("ODYSSEUS_NATS_SUBJECT", "odysseus.jobs.search")
CONFIG_PATH = Path(os.getenv("ODYSSEUS_SCHEDULE_PATH", "/app/config/research_targets.yml"))
STATE_PATH = Path(os.getenv("ODYSSEUS_SCHEDULER_STATE", "/data/scheduler-state.json"))
POLL_SECONDS = max(15, int(os.getenv("ODYSSEUS_SCHEDULER_POLL_SECONDS", "30")))
ENABLED = os.getenv("ODYSSEUS_SCHEDULER_ENABLED", "true").lower() == "true"


def load_config() -> list[dict[str, Any]]:
    raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    targets = raw.get("targets", [])
    if not isinstance(targets, list):
        raise ValueError("research_targets.yml: targets must be a list")
    return [item for item in targets if isinstance(item, dict)]


def load_state() -> dict[str, float]:
    if not STATE_PATH.exists():
        return {}
    try:
        raw = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(key): float(value) for key, value in raw.items()}


def save_state(state: dict[str, float]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(STATE_PATH)


def is_due(item: dict[str, Any], state: dict[str, float], now: float) -> bool:
    if not item.get("enabled", False):
        return False
    identifier = str(item.get("id") or item.get("target") or "")
    if not identifier:
        return False
    interval = max(5, int(item.get("interval_minutes", 60))) * 60
    return now - state.get(identifier, 0.0) >= interval


def build_job(item: dict[str, Any]) -> dict[str, Any]:
    target = str(item["target"])
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    return {
        "job_id": str(uuid.uuid4()),
        "query": str(item.get("query") or target),
        "profile": str(item.get("profile") or "specialist"),
        "requested_by": str(item.get("requested_by") or "odysseus-scheduler"),
        "metadata": {**metadata, "target": target, "schedule_id": str(item.get("id") or target)},
        "decision": {
            "route": "xeon_queue",
            "data_class": str(item.get("data_class") or "internal"),
            "reason": "Recurring research target from config/research_targets.yml",
        },
    }


async def run() -> None:
    if not ENABLED:
        logger.info("Scheduler disabled by ODYSSEUS_SCHEDULER_ENABLED=false")
        while True:
            await asyncio.sleep(3600)

    nc = await nats.connect(NATS_URL, name="odysseus-osint-scheduler", reconnect_time_wait=2, max_reconnect_attempts=-1)
    state = load_state()
    logger.info("Scheduler online; configuration=%s", CONFIG_PATH)

    try:
        while True:
            now = time.time()
            try:
                targets = load_config()
            except Exception:
                logger.exception("Could not load research schedule")
                await asyncio.sleep(POLL_SECONDS)
                continue

            changed = False
            for item in targets:
                if not is_due(item, state, now):
                    continue
                job = build_job(item)
                await nc.publish(NATS_SUBJECT, json.dumps(job, ensure_ascii=False).encode("utf-8"))
                identifier = str(item.get("id") or item.get("target"))
                state[identifier] = now
                changed = True
                logger.info("Published scheduled job %s for %s", job["job_id"], item.get("target"))
            if changed:
                await nc.flush()
                save_state(state)
            await asyncio.sleep(POLL_SECONDS)
    finally:
        await nc.drain()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
