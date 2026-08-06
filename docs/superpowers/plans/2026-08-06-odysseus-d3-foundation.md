# Odysseus D3 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Docker Compose foundation for the D3 edge-first search, identity, policy, VPN, Xeon, and SBOM architecture.

**Architecture:** SearXNG remains the search authority behind Traefik, OAuth2 Proxy, and Keycloak. The Odysseus API classifies specialist requests and publishes normalized NATS jobs, while the edge CLI sends ordinary tasks directly to providers and sensitive tasks to the Xeon path.

**Tech Stack:** Docker Compose, Traefik 3.7, Keycloak 26.5, OAuth2 Proxy 7.15, SearXNG 2026.7, FastAPI, NATS JetStream, Valkey, Qdrant, Gluetun, llama.cpp, pytest, Syft.

## Global Constraints

- SearXNG is the search authority, not the identity or evidence database.
- Keycloak is the identity authority and supports optional ORCID federation.
- Ordinary public tasks use direct provider routing; evidence and specialist tasks use the Xeon path.
- VPN search must fail closed with the Gluetun network namespace.
- Every upstream modification must appear in `docs/source-modifications/manifest.yaml`.
- Secrets and runtime-generated realm files must never enter Git.

---

### Task 1: Repository and Compose foundation

**Files:**
- Create: `compose.yaml`
- Create: `.env.example`
- Create: `Makefile`
- Create: `scripts/bootstrap.sh`
- Create: `scripts/render-config.sh`

**Interfaces:**
- Produces: Docker profiles `core`, `vpn`, `xeon`, and `observability`.

- [x] Define pinned container images and named volumes.
- [x] Generate secrets locally and render the Keycloak realm.
- [ ] Validate all profiles with `docker compose config` on a Docker-enabled host or CI runner.

### Task 2: Identity and reverse proxy

**Files:**
- Create: `deploy/traefik/dynamic/middlewares.yml`
- Create: `deploy/keycloak/realm-template.json`

**Interfaces:**
- Produces: OIDC client `odysseus-web`, realm roles, optional ORCID provider, and Traefik auth chain.

- [x] Protect SearXNG, API, Grafana, and Traefik dashboard.
- [x] Keep `/oauth2/` reachable for the login flow.

### Task 3: SearXNG profile UI

**Files:**
- Create: `services/searxng/Dockerfile`
- Create: `services/searxng/overlay/searx/templates/simple/search.html`
- Create: `deploy/searxng/settings.yml`
- Create: `config/search_profiles.yml`

**Interfaces:**
- Produces: Standard searches to SearXNG and specialist searches to `/odysseus/ui/search`.

- [x] Overlay only the upstream search form.
- [x] Record the exact modified upstream path in the manifest.

### Task 4: Policy and dispatch API

**Files:**
- Create: `services/odysseus-api/app/models.py`
- Create: `services/odysseus-api/app/policy.py`
- Create: `services/odysseus-api/app/queue.py`
- Create: `services/odysseus-api/app/main.py`
- Test: `services/odysseus-api/tests/test_policy.py`
- Test: `services/odysseus-api/tests/test_api.py`

**Interfaces:**
- Produces: `POST /v1/classify`, `POST /v1/search/dispatch`, and `GET /ui/search`.

- [x] Test standard, specialist, evidence override, and unknown-profile containment.
- [x] Publish normalized jobs to `odysseus.jobs.search`.

### Task 5: Edge client

**Files:**
- Create: `clients/edge-cli/edge.py`
- Test: `clients/edge-cli/tests/test_edge.py`

**Interfaces:**
- Produces: `route_prompt(prompt, preferred_cloud) -> RouteDecision`.

- [x] Route ordinary prompts to the configured cloud provider.
- [x] Route evidence markers to the Xeon API.

### Task 6: VPN and Xeon profiles

**Files:**
- Modify: `compose.yaml`
- Create: `deploy/searxng/settings-vpn.yml`

**Interfaces:**
- Produces: Gluetun network namespace, Qdrant, evidence storage, and llama.cpp runtime.

- [x] Use `network_mode: service:vpn-gateway` for fail-closed VPN search.
- [x] Keep specialist stores off published host ports.

### Task 7: Verification, SBOM, and documentation

**Files:**
- Create: `scripts/verify.sh`
- Create: `scripts/generate-sbom.sh`
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/sbom.yml`
- Create: `docs/architecture/D3.md`
- Create: `docs/source-modifications/manifest.yaml`

**Interfaces:**
- Produces: CI checks, SPDX/CycloneDX SBOM artifacts, ADRs, and operations runbook.

- [x] Compile Python and run pytest.
- [ ] Validate Compose on a Docker-enabled host or CI runner.
- [x] Generate committed source-declaration SPDX and CycloneDX SBOMs.
- [ ] Generate transitive Syft SBOMs in release CI.
