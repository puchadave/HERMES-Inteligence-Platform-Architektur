#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose --profile core --profile vpn --profile xeon --profile observability config >/dev/null
python3 -m compileall -q services/odysseus-api/app clients/edge-cli/edge.py
python3 -m pytest services/odysseus-api/tests clients/edge-cli/tests -q

echo "Verification passed."
