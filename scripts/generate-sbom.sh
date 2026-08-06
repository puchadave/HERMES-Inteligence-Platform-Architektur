#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python3 scripts/generate-source-sbom.py

command -v syft >/dev/null 2>&1 || {
  echo "syft is required: https://github.com/anchore/syft" >&2
  exit 1
}
mkdir -p sbom
syft dir:. -o spdx-json=sbom/odysseus.spdx.json
syft dir:. -o cyclonedx-json=sbom/odysseus.cyclonedx.json
echo "Source and transitive SBOMs written to sbom/."
