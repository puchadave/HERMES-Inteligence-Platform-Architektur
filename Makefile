SHELL := /usr/bin/env bash
COMPOSE := docker compose

.PHONY: bootstrap render up up-vpn up-xeon up-observability down logs ps test verify sbom config

bootstrap:
	./scripts/bootstrap.sh

render:
	./scripts/render-config.sh

up: render
	$(COMPOSE) --profile core up -d --build

up-vpn: render
	$(COMPOSE) --profile core --profile vpn up -d --build

up-xeon: render
	$(COMPOSE) --profile core --profile xeon up -d --build

up-observability: render
	$(COMPOSE) --profile core --profile observability up -d --build

down:
	$(COMPOSE) --profile core --profile vpn --profile xeon --profile observability down

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

test:
	python3 -m pytest services/odysseus-api/tests clients/edge-cli/tests -q

verify: render
	./scripts/verify.sh

sbom:
	./scripts/generate-sbom.sh

config: render
	$(COMPOSE) --profile core --profile vpn --profile xeon --profile observability config
