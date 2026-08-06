# Reproducibility

## Source state

- Repository commits are the canonical source state.
- SearXNG uses the pinned image tag recorded in `docs/source-modifications/manifest.yaml`.
- Container versions are pinned in `compose.yaml`.
- Python dependencies are pinned in component `pyproject.toml` files.

## Rebuild

```bash
git clone https://github.com/puchadave/HERMES-Inteligence-Platform-Architektur.git
cd HERMES-Inteligence-Platform-Architektur
cp .env.example .env
./scripts/bootstrap.sh
make verify
make up
```

## Verification evidence

CI records:

- test output;
- Compose validation;
- image build status;
- generated SPDX and CycloneDX SBOM artifacts on release tags.

## Runtime data

Runtime secrets, model files, case data, and generated Keycloak realm files are excluded from Git. Reproducing a production installation therefore requires the repository commit, separately backed-up secrets, model files, and Docker volumes.
