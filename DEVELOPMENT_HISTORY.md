# Development History

## 2026-08-01 to 2026-08-05: exploration

The project evolved from a local Hermes/OSINT workstation concept into a multi-agent platform. Early experiments covered Ollama, llama.cpp, Hermes Agent, local GGUF models, SearXNG extensions, Maltego-compatible research workflows, and document-backed RAG.

## 2026-08-06: D architecture selection

The target hardware was fixed as an older HP Xeon system upgraded to 64 GB RAM in eight-channel mode. The architecture was changed from a single large local model to an edge-first model:

- small clients handle conversation, local sorting, and routing;
- ordinary public tasks use configured external providers directly;
- specialist, sensitive, RAG-heavy, and evidence-bound tasks use the Xeon core.

## 2026-08-06: D3 approval

The approved D3 design established:

- SearXNG as Search Authority;
- Keycloak as Identity Authority;
- optional ORCID federation;
- Traefik and OAuth2 Proxy for authenticated routing;
- a ProtonVPN-compatible isolated SearXNG profile;
- NATS for future worker federation;
- Qdrant, local GGUF inference, evidence storage, monitoring, SBOM, and source-modification records.

## 2026-08-06: repository foundation

The first implementation added the Docker Compose profiles, SearXNG UI overlay, deterministic policy API, edge CLI, tests, CI, SBOM workflow, architecture decisions, runbook, and modification manifest.
