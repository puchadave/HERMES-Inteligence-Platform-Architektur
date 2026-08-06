#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

[[ -f .env ]] || { echo "Missing .env; run ./scripts/bootstrap.sh" >&2; exit 1; }
set -a
# shellcheck disable=SC1091
source .env
set +a

mkdir -p runtime/keycloak
python3 - <<'PY'
from pathlib import Path
import json
import os

template = Path('deploy/keycloak/realm-template.json').read_text(encoding='utf-8')
keys = [
    'OAUTH2_PROXY_CLIENT_SECRET', 'SEARCH_HOST', 'API_HOST', 'GRAFANA_HOST',
    'ORCID_CLIENT_ID', 'ORCID_CLIENT_SECRET'
]
for key in keys:
    template = template.replace('${' + key + '}', os.getenv(key, ''))
template = template.replace('${ORCID_ENABLED}', os.getenv('ORCID_ENABLED', 'false').lower())
parsed = json.loads(template)
Path('runtime/keycloak/realm.json').write_text(json.dumps(parsed, indent=2) + '\n', encoding='utf-8')
PY
