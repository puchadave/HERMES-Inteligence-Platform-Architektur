# Source SBOM Verification · 2026-08-06

- Generator: `scripts/generate-source-sbom.py`
- CycloneDX: `sbom/odysseus-source.cyclonedx.json`
- SPDX: `sbom/odysseus-source.spdx.json`
- Declared components in each format: 24
- Inputs: `compose.yaml`, project Dockerfiles, and Python `pyproject.toml` dependency declarations
- Result: both JSON documents parsed successfully and regenerated deterministically in the local verification environment

These committed documents are top-level source-declaration SBOMs. The release workflow separately generates transitive filesystem SBOMs with Syft.
