from pathlib import Path
from typing import Any

import yaml

from .models import DataClass, Route, SearchDecision


DEFAULT_PROFILES: dict[str, dict[str, str]] = {
    "standard": {"route": "searxng", "data_class": "public"},
    "social": {"route": "xeon_queue", "data_class": "public"},
    "domains": {"route": "xeon_queue", "data_class": "public"},
    "reverse_contact": {"route": "xeon_queue", "data_class": "confidential"},
    "documents": {"route": "xeon_queue", "data_class": "internal"},
    "media": {"route": "xeon_queue", "data_class": "internal"},
    "threat_intel": {"route": "xeon_queue", "data_class": "internal"},
    "specialist": {"route": "xeon_queue", "data_class": "evidence"},
}


class PolicyEngine:
    def __init__(self, profiles: dict[str, dict[str, Any]] | None = None) -> None:
        self.profiles = profiles or DEFAULT_PROFILES

    @classmethod
    def from_yaml(cls, path: str) -> "PolicyEngine":
        config_path = Path(path)
        if not config_path.exists():
            return cls()
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        return cls(data.get("profiles") or DEFAULT_PROFILES)

    def decide(self, profile: str, query: str) -> SearchDecision:
        normalized = profile.strip().lower()
        config = self.profiles.get(normalized)
        if config is None:
            normalized = "specialist"
            config = self.profiles[normalized]
            reason = "Unknown profile was contained and routed to the specialist queue."
        else:
            reason = f"Profile '{normalized}' maps to its configured deterministic route."

        lowered = query.lower()
        sensitive_markers = ("evidence", "beweismittel", "fallakte", "private email", "roh-email")
        if any(marker in lowered for marker in sensitive_markers):
            return SearchDecision(
                profile=normalized,
                route=Route.XEON_QUEUE,
                data_class=DataClass.EVIDENCE,
                reason="Evidence marker forces local Xeon processing.",
            )

        return SearchDecision(
            profile=normalized,
            route=Route(config["route"]),
            data_class=DataClass(config["data_class"]),
            reason=reason,
        )
