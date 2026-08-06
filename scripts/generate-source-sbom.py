#!/usr/bin/env python3
"""Generate deterministic source-declaration SBOMs from Compose and pyproject files.

This is not an image-layer SBOM. Release CI uses Syft for transitive filesystem and
container contents. These files document the exact top-level components declared by
this repository before images are built.
"""
from __future__ import annotations

import hashlib
import json
import re
import tomllib
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-08-06T00:00:00Z"


def split_image(image: str) -> tuple[str, str]:
    if "@" in image:
        return image.split("@", 1)
    last = image.rsplit("/", 1)[-1]
    if ":" in last:
        name, version = image.rsplit(":", 1)
        return name, version
    return image, "latest"


def split_requirement(requirement: str) -> tuple[str, str]:
    match = re.match(r"^([A-Za-z0-9_.-]+)(?:\[[^]]+\])?==(.+)$", requirement)
    if match:
        return match.group(1), match.group(2)
    return requirement, "unspecified"


def compose_documents() -> list[tuple[Path, dict]]:
    documents: list[tuple[Path, dict]] = []
    for path in sorted(ROOT.glob("compose*.yaml")):
        parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(parsed, dict) and isinstance(parsed.get("services"), dict):
            documents.append((path, parsed))
    return documents


def collect() -> list[dict[str, str]]:
    components: list[dict[str, str]] = []
    compose_args: dict[str, str] = {}

    for _, compose in compose_documents():
        for service, config in sorted(compose["services"].items()):
            if not isinstance(config, dict):
                continue
            image = config.get("image")
            if image:
                name, version = split_image(str(image))
                components.append({"type": "container", "name": name, "version": version, "scope": service})
            elif "build" in config:
                components.append({"type": "application", "name": f"odysseus/{service}", "version": "0.1.0", "scope": service})

            build = config.get("build")
            if isinstance(build, dict):
                for key, value in (build.get("args") or {}).items():
                    compose_args[str(key)] = str(value)

    for dockerfile in sorted(ROOT.glob("**/Dockerfile")):
        if ".venv" in dockerfile.parts:
            continue
        args = dict(compose_args)
        for raw_line in dockerfile.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line.upper().startswith("ARG "):
                declaration = line[4:]
                key, _, value = declaration.partition("=")
                args.setdefault(key, value)
            if line.upper().startswith("FROM "):
                image = line.split()[1]
                for key, value in args.items():
                    image = image.replace("${" + key + "}", value)
                name, version = split_image(image)
                components.append({
                    "type": "container",
                    "name": name,
                    "version": version,
                    "scope": str(dockerfile.relative_to(ROOT)),
                })

    for pyproject in sorted(ROOT.glob("**/pyproject.toml")):
        if ".venv" in pyproject.parts:
            continue
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        project = data.get("project", {})
        for requirement in project.get("dependencies", []):
            name, version = split_requirement(requirement)
            components.append({"type": "library", "name": name, "version": version, "scope": str(pyproject.parent.relative_to(ROOT))})

    dedup = {(c["type"], c["name"], c["version"], c["scope"]): c for c in components}
    return [dedup[key] for key in sorted(dedup)]


def serial(components: list[dict[str, str]]) -> str:
    payload = json.dumps(components, sort_keys=True, separators=(",", ":"))
    return f"urn:uuid:{uuid5(NAMESPACE_URL, payload)}"


def cyclonedx(components: list[dict[str, str]]) -> dict:
    cdx_components = []
    for component in components:
        purl_type = "docker" if component["type"] == "container" else "pypi" if component["type"] == "library" else "generic"
        cdx_components.append({
            "type": component["type"],
            "name": component["name"],
            "version": component["version"],
            "bom-ref": f"{component['type']}:{component['scope']}:{component['name']}@{component['version']}",
            "purl": f"pkg:{purl_type}/{component['name']}@{component['version']}",
            "properties": [{"name": "odysseus:scope", "value": component["scope"]}],
        })
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial(components),
        "version": 1,
        "metadata": {
            "timestamp": DATE,
            "component": {"type": "application", "name": "Odysseus D3", "version": "0.2.0"},
            "properties": [{"name": "odysseus:sbom-kind", "value": "source-declaration"}],
        },
        "components": cdx_components,
    }


def spdx(components: list[dict[str, str]]) -> dict:
    packages = []
    for index, component in enumerate(components, start=1):
        packages.append({
            "name": component["name"],
            "SPDXID": f"SPDXRef-Package-{index}",
            "versionInfo": component["version"],
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "comment": f"scope={component['scope']};type={component['type']}",
        })
    digest = hashlib.sha256(json.dumps(components, sort_keys=True).encode()).hexdigest()
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "Odysseus-D3-source-declaration",
        "documentNamespace": f"https://puchalla.pro/sbom/odysseus/{digest}",
        "creationInfo": {"created": DATE, "creators": ["Tool: Odysseus source SBOM generator"]},
        "documentDescribes": [package["SPDXID"] for package in packages],
        "packages": packages,
        "comment": "Top-level source declarations only; release CI generates transitive Syft SBOMs.",
    }


def main() -> None:
    components = collect()
    out = ROOT / "sbom"
    out.mkdir(exist_ok=True)
    (out / "odysseus-source.cyclonedx.json").write_text(json.dumps(cyclonedx(components), separators=(",", ":")) + "\n")
    (out / "odysseus-source.spdx.json").write_text(json.dumps(spdx(components), separators=(",", ":")) + "\n")
    print(f"Wrote source-declaration SBOMs for {len(components)} components.")


if __name__ == "__main__":
    main()
