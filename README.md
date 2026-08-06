# HERMES Intelligence Platform Architecture · Odysseus D3

Odysseus D3 is an edge-first, federated research and evidence platform. SearXNG is the search authority, Keycloak is the identity authority, the HP Xeon/64 GB node is the specialist analysis core, and small clients route ordinary tasks directly to configured AI providers.

## Architecture

```text
Clients / Mini-LLM Router
          │
          ├── ordinary public tasks ──► Gemini / OpenAI adapters
          │
          └── specialist or sensitive tasks
                         │
                         ▼
Keycloak ─► Traefik ─► SearXNG ─► Odysseus API ─► NATS JetStream
                                                         │
                         ┌───────────────────────────────┼───────────────────────────────┐
                         │                               │                               │
                  OpenOSINT MCP                   BBOT passive pipeline            GitHub MCP
                         │                               │                               │
                         └──────────────────► OSINT Worker ◄────────────────────────────┘
                                                         │
                                               JSON / Markdown / SHA-256
                                                         │
                                         authenticated Result API / SearXNG
```

## Included in this foundation

- SearXNG with an Odysseus search-profile selector.
- Keycloak + OAuth2 Proxy login in front of SearXNG and the API.
- Optional ProtonVPN-isolated SearXNG instance through Gluetun.
- FastAPI policy and dispatch service with durable JetStream publication.
- Edge CLI with local routing and OpenAI, Gemini, or Xeon execution paths.
- OpenOSINT 2.25.0 exposed as a Streamable HTTP MCP server.
- Official GitHub MCP Server 1.0.5 in read-only HTTP mode.
- Durable JetStream worker with deterministic target classification, explicit acknowledgements, retry limits, and acknowledgement heartbeats.
- Optional passive BBOT pipeline based on the agent pattern from `esandeepchoudary/osint_automation_using_AI_agents`.
- Recurring scheduler that reloads `config/research_targets.yml` without restart.
- Deterministic JSON and Markdown reports with SHA-256 manifests.
- Authenticated API endpoints for completed reports and job listings.
- Optional Qdrant, MinIO, llama.cpp, Prometheus, Loki, and Grafana profiles.
- CI, tests, committed source-declaration SBOMs, release SBOM generation, source-modification manifest, ADRs, and operations documentation.

## Start locally

```bash
cp .env.example .env
./scripts/bootstrap.sh
make up
```

Open:

- `http://search.localhost`
- `http://auth.localhost`
- `http://api.localhost/healthz`

Default local administrator credentials are written to `.env` by `scripts/bootstrap.sh`.

## Background research profile

The research profile starts OpenOSINT MCP, GitHub MCP, the JetStream worker, and the recurring scheduler:

```bash
make config-research
make up-research
make logs
```

The worker consumes durable jobs from `odysseus.jobs.search`, discovers the MCP tools that are actually available, invokes the matching OpenOSINT tools, optionally runs passive BBOT for domain targets, and writes artifacts to the `research-data` Docker volume. Successful processing is explicitly acknowledged. Failed jobs are redelivered up to `ODYSSEUS_MAX_DELIVERIES` and then terminated rather than looping forever like a particularly stubborn office printer.

Scheduled targets live in `config/research_targets.yml`. Entries are disabled by default. Set `enabled: true` only for a target that should be checked repeatedly. The minimum interval is five minutes.

Optional provider keys and worker switches are documented in `.env.example`. Keyless WHOIS, DNS, subdomain, username, GitHub, paste, and dork-generation tools remain available without paid APIs.

### Read completed results

All result routes remain behind the existing Keycloak/OAuth2 Proxy chain:

```text
GET /odysseus/v1/jobs
GET /odysseus/v1/jobs/<job-id>
GET /odysseus/v1/jobs/<job-id>/report
```

The JSON document is the canonical machine-readable record. The Markdown representation is generated deterministically from the same result and both files are covered by `manifest.sha256`.

## Optional profiles

```bash
make up-vpn          # ProtonVPN-isolated SearXNG node
make up-xeon         # Qdrant, evidence store, llama.cpp runtime
make up-research     # OpenOSINT MCP, GitHub MCP, worker, scheduler
make up-observability
```

## Verification

```bash
make test
make verify
make sbom
make config-research
```

## Security model

- Browser login is external to SearXNG, reducing upstream patching.
- Specialist requests are classified by deterministic policy before dispatch.
- OpenOSINT and GitHub MCP remain on the internal backend network.
- GitHub MCP starts read-only and records command traffic to its own log volume.
- Paid or credentialed OpenOSINT tools are skipped unless their key is configured.
- BBOT is disabled by default and, when enabled, requires passive modules.
- JetStream provides persisted jobs, explicit acknowledgements, bounded redelivery, and result publication.
- VPN search loses connectivity when the tunnel fails.
- Secrets are generated locally and excluded from Git.
- Evidence and specialist data remain on the Xeon profile unless explicitly routed otherwise.

See `docs/architecture/D3.md`, `docs/architecture/MCP-AUTOMATION.md`, `docs/operations/RUNBOOK.md`, and `docs/source-modifications/manifest.yaml`.
