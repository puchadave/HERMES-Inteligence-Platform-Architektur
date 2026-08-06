# Operations Runbook

## Bootstrap

```bash
cp .env.example .env
./scripts/bootstrap.sh
```

## Core startup

```bash
docker compose --profile core up -d --build
docker compose ps
```

## VPN profile

Populate `WIREGUARD_PRIVATE_KEY` and `WIREGUARD_ADDRESSES` in `.env`, then:

```bash
docker compose --profile core --profile vpn up -d --build
docker compose logs -f vpn-gateway
```

Do not expose the VPN SearXNG port directly. It shares the gateway namespace and is intended for controlled internal dispatch.

## Xeon profile

Place a GGUF file in `models/`, set `LOCAL_LLM_MODEL_FILE`, and run:

```bash
docker compose --profile core --profile xeon up -d --build
```

## Backup

Back up Docker volumes for Keycloak PostgreSQL, NATS JetStream, Qdrant, and evidence storage. Store `.env` separately from the repository.

## Recovery test

1. Restore volumes to a clean Docker host.
2. Restore `.env`.
3. Run `./scripts/render-config.sh`.
4. Run `make verify`.
5. Start the core and verify login, SearXNG search, API health, and NATS health.
