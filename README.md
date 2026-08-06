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
Keycloak ─► Traefik ─► SearXNG ─► Odysseus API ─► NATS ─► Xeon workers
                                      │
                                      ├── Qdrant RAG
                                      └── Evidence object store
```

## Included in this foundation

- SearXNG with an Odysseus search-profile selector.
- Keycloak + OAuth2 Proxy login in front of SearXNG and the API.
- Optional ProtonVPN-isolated SearXNG instance through Gluetun.
- FastAPI policy and dispatch service with NATS job publication.
- Edge CLI with local routing and OpenAI, Gemini, or Xeon execution paths.
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

## Optional profiles

```bash
make up-vpn          # ProtonVPN-isolated SearXNG node
make up-xeon         # Qdrant, evidence store, llama.cpp runtime
make up-observability
```

## Verification

```bash
make test
make verify
make sbom
```

## Security model

- Browser login is external to SearXNG, reducing upstream patching.
- Specialist requests are classified by deterministic policy before dispatch.
- VPN search loses connectivity when the tunnel fails.
- Secrets are generated locally and excluded from Git.
- Evidence and specialist data remain on the Xeon profile unless explicitly routed otherwise.

See `docs/architecture/D3.md`, `docs/operations/RUNBOOK.md`, and `docs/source-modifications/manifest.yaml`.
