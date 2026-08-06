#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

random_hex() { openssl rand -hex "$1"; }
random_b64() { openssl rand -base64 "$1" | tr -d '\n'; }

replace_change_me() {
  local key="$1" value="$2"
  python3 - "$key" "$value" <<'PY'
from pathlib import Path
import sys
key, value = sys.argv[1], sys.argv[2]
path = Path('.env')
lines = path.read_text().splitlines()
out = []
for line in lines:
    if line.startswith(key + '=') and line.split('=', 1)[1] == 'CHANGE_ME':
        out.append(f'{key}={value}')
    else:
        out.append(line)
path.write_text('\n'.join(out) + '\n')
PY
}

replace_change_me POSTGRES_PASSWORD "$(random_hex 24)"
replace_change_me KEYCLOAK_ADMIN_PASSWORD "$(random_hex 24)"
replace_change_me KEYCLOAK_DB_PASSWORD "$(random_hex 24)"
replace_change_me OAUTH2_PROXY_CLIENT_SECRET "$(random_hex 32)"
replace_change_me OAUTH2_PROXY_COOKIE_SECRET "$(random_b64 32)"
replace_change_me SEARXNG_SECRET "$(random_hex 32)"
replace_change_me QDRANT_API_KEY "$(random_hex 32)"
replace_change_me MINIO_ROOT_PASSWORD "$(random_hex 24)"
replace_change_me GRAFANA_ADMIN_PASSWORD "$(random_hex 24)"
replace_change_me NATS_PASSWORD "$(random_hex 24)"

./scripts/render-config.sh
printf 'Bootstrap complete. Secrets remain only in .env and runtime/.\n'
