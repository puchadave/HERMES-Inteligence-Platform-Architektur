# ADR-0005: SBOM and provenance

- Status: Accepted
- Date: 2026-08-06

Every release produces SPDX and CycloneDX SBOMs. GitHub Actions also records dependency review, container build metadata, and the source-modification manifest. Generated SBOMs are build artifacts, not hand-edited files.
