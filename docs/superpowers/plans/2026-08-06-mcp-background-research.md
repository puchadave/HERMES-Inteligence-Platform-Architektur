# MCP Background Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add OpenOSINT MCP, the official GitHub MCP server, a recurring scheduler, and a deterministic background research worker to Odysseus D3.

**Architecture:** SearXNG and the API publish jobs to NATS. A persistent worker classifies each target, invokes real OpenOSINT tools over Streamable HTTP MCP, optionally runs passive BBOT, enriches GitHub repository targets through the official read-only GitHub MCP server, and emits hashed JSON/Markdown artifacts.

**Tech Stack:** Docker Compose, Python 3.12, NATS, OpenOSINT 2.25.0, Supergateway 3.4.3, GitHub MCP Server 1.0.5, BBOT 2.7.2, pytest.

## Global Constraints

- Keep SearXNG as search authority and NATS as the asynchronous transport.
- Keep MCP servers on the internal backend network.
- GitHub MCP must remain read-only.
- Paid OpenOSINT tools run only when their required secret is present.
- BBOT must require passive modules and remain disabled by default.
- Every job must generate deterministic JSON, Markdown, and SHA-256 artifacts.

---

### Task 1: OpenOSINT MCP transport

**Files:**
- Create: `services/openosint-mcp/Dockerfile`
- Create: `compose.research.yaml`

- [x] Build an image containing OpenOSINT and its keyless binaries.
- [x] Convert OpenOSINT stdio MCP to Streamable HTTP.
- [x] Add a health endpoint and persistent report volume.

### Task 2: Official GitHub MCP server

**Files:**
- Create: `config/mcp_servers.json`
- Modify: `compose.research.yaml`

- [x] Add the official image in native HTTP mode.
- [x] Restrict it to read-only repository-related toolsets.
- [x] Keep the PAT outside source control.

### Task 3: Deterministic research worker

**Files:**
- Create: `services/osint-worker/app/mcp_client.py`
- Create: `services/osint-worker/app/planner.py`
- Create: `services/osint-worker/app/worker.py`
- Create: `services/osint-worker/app/reporting.py`
- Create: `services/osint-worker/app/source_intelligence.py`

- [x] Implement MCP initialization, tool discovery, and tool calls.
- [x] Classify email, username, domain, IP, phone, URL, and text targets.
- [x] Run tools with bounded parallelism and independent failure records.
- [x] Add passive BBOT compatibility.
- [x] Add GitHub repository enrichment through `get_file_contents`.
- [x] Write JSON, Markdown, and SHA-256 manifests.

### Task 4: Recurring scheduler

**Files:**
- Create: `services/osint-worker/app/scheduler.py`
- Create: `config/research_targets.yml`

- [x] Reload target configuration on every polling cycle.
- [x] Persist last-run state atomically.
- [x] Publish due jobs to NATS without restarting containers.

### Task 5: Verification and operations

**Files:**
- Create: `services/osint-worker/tests/test_planner.py`
- Create: `services/osint-worker/tests/test_source_intelligence.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `Makefile`
- Modify: `.env.example`
- Modify: `README.md`
- Create: `docs/architecture/MCP-AUTOMATION.md`

- [x] Test target classification and planning.
- [x] Test GitHub repository URL parsing.
- [x] Validate both Compose files in CI.
- [x] Build the worker and OpenOSINT MCP images in CI.
- [x] Document startup, storage, and failure behavior.
