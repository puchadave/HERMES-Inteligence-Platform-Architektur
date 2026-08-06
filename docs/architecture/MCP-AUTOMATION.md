# MCP Background Research Architecture

## Objective

The research profile turns Odysseus from a dispatch-only foundation into a continuously running collection pipeline. It keeps language-model reasoning separate from deterministic tool execution and stores every result as reproducible artifacts.

## Components

```text
SearXNG / Edge Client / Scheduler
               │
               ▼
        Odysseus API
               │
               ▼
      NATS odysseus.jobs.search
               │
               ▼
         OSINT Worker
        ┌──────┼────────┐
        │      │        │
 OpenOSINT MCP BBOT GitHub MCP
        │      │        │
        └──────┼────────┘
               ▼
 JSON + Markdown + SHA-256 manifest
```

### OpenOSINT MCP

`services/openosint-mcp/Dockerfile` installs OpenOSINT 2.25.0 and its keyless command-line dependencies. OpenOSINT natively exposes its tools over stdio. Supergateway 3.4.3 converts the stdio transport to a stateful Streamable HTTP endpoint at `/mcp`.

The worker discovers available tools at runtime through `tools/list`; no result is invented when a binary, API key, or MCP tool is unavailable. Optional provider tools remain skipped unless the required secret exists.

### GitHub MCP

The official `ghcr.io/github/github-mcp-server:v1.0.5` image runs in native HTTP mode. It is configured read-only and exposes only repository, issue, pull-request, and Actions toolsets. The token is sent by the MCP client as a bearer token; it is not committed to the repository.

GitHub URLs in incoming jobs trigger repository-root enrichment through `get_file_contents`. Ordinary public username or keyword searches continue to use OpenOSINT's public GitHub search tool.

### BBOT compatibility pipeline

The worker adopts the orchestration pattern from `esandeepchoudary/osint_automation_using_AI_agents` without importing its Google ADK runtime. Domain jobs can invoke BBOT with the flags `safe`, `subdomain-enum`, `affiliates`, `email-enum`, and `social-enum`, while requiring the `passive` flag.

BBOT is disabled by default because dependency installation and scans are substantially heavier than keyless MCP calls. Enable it with `ODYSSEUS_ENABLE_BBOT=true`.

### Scheduler

`osint-scheduler` reloads `config/research_targets.yml` every poll. A target is dispatched only when `enabled: true` and its configured interval has elapsed. Scheduler state is written atomically to `/data/scheduler-state.json`.

### Reports

Every job receives its own directory:

```text
/data/jobs/<job-id>/
├── result.json
├── summary.md
├── manifest.sha256
└── bbot/                 # only when BBOT is enabled for a domain job
```

The JSON file is the canonical machine-readable record. The Markdown file is a deterministic human-readable rendering, not an LLM-generated interpretation. `manifest.sha256` records the hashes of both files.

## Data flow

1. The API or scheduler publishes a normalized job to `odysseus.jobs.search`.
2. The worker extracts and classifies the target.
3. The deterministic planner selects OpenOSINT tools.
4. The worker asks the MCP server which tools are actually available.
5. Keyless and configured optional tools run with bounded parallelism.
6. A domain target optionally receives a passive BBOT scan.
7. A GitHub repository URL optionally receives read-only GitHub MCP context.
8. Results are serialized, hashed, and published to `odysseus.results.search`.

## Operational commands

```bash
cp .env.example .env
./scripts/bootstrap.sh
make config-research
make up-research
make logs
```

Enable a recurring target by editing `config/research_targets.yml` and changing its `enabled` field to `true`. No container restart is required.

## Failure behavior

- An unavailable MCP tool is recorded as `unavailable`.
- A missing optional API key is recorded as `skipped`.
- A failed tool is recorded as `error`; other tools continue.
- A BBOT timeout or module failure does not discard MCP results.
- A GitHub MCP failure is preserved in the report and does not stop OpenOSINT collection.
- NATS reconnects indefinitely after transient connection loss.
