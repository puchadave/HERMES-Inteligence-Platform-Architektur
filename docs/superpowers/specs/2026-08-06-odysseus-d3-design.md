# Odysseus D3 Design Specification

## Objective

Create a reproducible Docker Compose platform that uses SearXNG as the authenticated search authority, an HP Xeon server with 64 GB RAM as the specialist processing core, and small edge clients for 80/20 routing between external providers and local processing.

## Component boundaries

- Traefik exposes HTTP entry points and applies reusable middleware.
- Keycloak owns user identities, roles, and optional ORCID federation.
- OAuth2 Proxy translates the Keycloak session into reverse-proxy authentication headers.
- SearXNG owns metasearch and search-profile selection.
- Odysseus API owns deterministic classification and specialist dispatch.
- NATS JetStream owns asynchronous job transport.
- Qdrant owns local vector collections.
- The evidence object store owns original artifacts and case exports.
- llama.cpp owns local GGUF inference.
- The edge client owns the ordinary-provider versus Xeon routing decision.

## Deployment profiles

- `core`: identity, search, policy, queue, cache, and reverse proxy.
- `vpn`: ProtonVPN-compatible Gluetun gateway plus an isolated SearXNG process.
- `xeon`: Qdrant, evidence store, and llama.cpp runtime.
- `observability`: Prometheus, Loki, and Grafana.

## Security invariants

1. Credentials are generated into `.env`, never committed.
2. Runtime Keycloak configuration is rendered locally and ignored by Git.
3. Specialist stores expose no host ports by default.
4. The VPN search process shares the VPN gateway namespace and cannot silently fall back.
5. Unknown search profiles are contained and routed to the specialist queue.
6. Evidence markers override public routing.
7. Every modified upstream file is recorded with its pinned baseline.

## Acceptance criteria

- The Python policy and API tests pass.
- Python modules compile without errors.
- YAML and JSON configuration parse successfully.
- Docker Compose configuration validates in CI for all profiles.
- The custom SearXNG and Odysseus API images build in CI.
- Release workflows generate SPDX and CycloneDX SBOM artifacts.
