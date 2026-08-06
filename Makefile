SHELL := /usr/bin/env bash
COMPOSE := docker compose
RESEARCH_COMPOSE := $(COMPOSE) -f compose.yaml -f compose.research.yaml

.PHONY: bootstrap render up up-vpn up-xeon up-research up-observability down logs ps test verify sbom config config-research

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

up-research: render
	$(RESEARCH_COMPOSE) --profile core --profile research up -d --build

up-observability: render
	$(COMPOSE) --profile core --profile observability up -d --build

down:
	$(RESEARCH_COMPOSE) --profile core --profile vpn --profile xeon --profile research --profile observability down

logs:
	$(RESEARCH_COMPOSE) logs -f --tail=200

ps:
	$(RESEARCH_COMPOSE) ps

test:
	python3 -m pytest services/odysseus-api/tests clients/edge-cli/tests services/osint-worker/tests -q

verify: render
	./scripts/verify.sh

sbom:
	./scripts/generate-sbom.sh

config: render
	$(COMPOSE) --profile core --profile vpn --profile xeon --profile observability config

config-research: render
	$(RESEARCH_COMPOSE) --profile core --profile research config
