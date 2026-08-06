from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlparse


class TargetKind(StrEnum):
    EMAIL = "email"
    USERNAME = "username"
    DOMAIN = "domain"
    IP = "ip"
    PHONE = "phone"
    URL = "url"
    TEXT = "text"


@dataclass(frozen=True, slots=True)
class ToolCall:
    name: str
    arguments: dict[str, object]
    optional_secret: str | None = None


_EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_URL = re.compile(r"https?://[^\s<>'\"]+", re.IGNORECASE)
_DOMAIN = re.compile(r"(?<![@\w-])(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}(?![\w-])", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\w)\+?[1-9][0-9 .()/-]{7,20}[0-9](?!\w)")
_USERNAME = re.compile(r"(?<!\w)@([A-Za-z0-9_.-]{2,64})(?!\w)")


def extract_target(query: str) -> str:
    value = query.strip()
    for pattern in (_EMAIL, _URL, _DOMAIN, _PHONE):
        match = pattern.search(value)
        if match:
            return match.group(0).rstrip(".,;:)")
    username = _USERNAME.search(value)
    if username:
        return username.group(1)
    return value


def classify_target(target: str) -> TargetKind:
    value = target.strip()
    if _EMAIL.fullmatch(value):
        return TargetKind.EMAIL
    if _URL.fullmatch(value):
        return TargetKind.URL
    try:
        ipaddress.ip_address(value)
        return TargetKind.IP
    except ValueError:
        pass
    if _PHONE.fullmatch(value):
        return TargetKind.PHONE
    if _DOMAIN.fullmatch(value):
        return TargetKind.DOMAIN
    if re.fullmatch(r"[A-Za-z0-9_.-]{2,64}", value):
        return TargetKind.USERNAME
    return TargetKind.TEXT


def normalize_target(target: str, kind: TargetKind) -> str:
    value = target.strip()
    if kind is TargetKind.URL:
        parsed = urlparse(value)
        return value if parsed.scheme and parsed.netloc else f"https://{value}"
    if kind is TargetKind.DOMAIN:
        return value.lower().rstrip(".")
    if kind is TargetKind.EMAIL:
        return value.lower()
    if kind is TargetKind.PHONE:
        return re.sub(r"[^+0-9]", "", value)
    return value


def build_plan(target: str, *, include_paid: bool = False) -> list[ToolCall]:
    kind = classify_target(target)
    value = normalize_target(target, kind)

    if kind is TargetKind.EMAIL:
        calls = [
            ToolCall("search_email", {"email": value, "json_output": True}),
            ToolCall("search_breach", {"email": value, "json_output": True}, "HIBP_API_KEY"),
            ToolCall("search_paste", {"query": value, "json_output": True}),
            ToolCall("search_github", {"query": value, "json_output": True}),
            ToolCall("generate_dorks", {"target": value, "json_output": True}),
        ]
    elif kind is TargetKind.USERNAME:
        calls = [
            ToolCall("search_username", {"username": value, "json_output": True}),
            ToolCall("search_paste", {"query": value, "json_output": True}),
            ToolCall("search_github", {"query": value, "json_output": True}),
            ToolCall("generate_dorks", {"target": value, "json_output": True}),
        ]
    elif kind is TargetKind.DOMAIN:
        calls = [
            ToolCall("search_whois", {"domain": value, "json_output": True}),
            ToolCall("search_dns", {"domain": value, "json_output": True}),
            ToolCall("search_domain", {"domain": value, "json_output": True}),
            ToolCall("search_github", {"query": value, "json_output": True}),
            ToolCall("search_virustotal", {"target": value, "json_output": True}, "VIRUSTOTAL_API_KEY"),
            ToolCall("search_censys", {"target": value, "json_output": True}, "CENSYS_API_ID"),
            ToolCall("search_shodan", {"query": value, "json_output": True}, "SHODAN_API_KEY"),
        ]
    elif kind is TargetKind.IP:
        calls = [
            ToolCall("search_ip", {"ip": value, "json_output": True}),
            ToolCall("search_abuseipdb", {"ip": value, "json_output": True}, "ABUSEIPDB_API_KEY"),
            ToolCall("search_ip2location", {"ip": value, "json_output": True}, "IP2LOCATION_API_KEY"),
            ToolCall("search_virustotal", {"target": value, "json_output": True}, "VIRUSTOTAL_API_KEY"),
            ToolCall("search_shodan", {"query": value, "json_output": True}, "SHODAN_API_KEY"),
            ToolCall("search_censys", {"target": value, "json_output": True}, "CENSYS_API_ID"),
        ]
    elif kind is TargetKind.PHONE:
        calls = [
            ToolCall("search_phone", {"phone": value, "json_output": True}),
            ToolCall("generate_dorks", {"target": value, "json_output": True}),
        ]
    elif kind is TargetKind.URL:
        calls = [
            ToolCall("search_virustotal", {"target": value, "json_output": True}, "VIRUSTOTAL_API_KEY"),
            ToolCall("scrape_url", {"url": value, "json_output": True}, "BRIGHTDATA_API_KEY"),
        ]
    else:
        calls = [
            ToolCall("search_github", {"query": value, "json_output": True}),
            ToolCall("generate_dorks", {"target": value, "json_output": True}),
            ToolCall("search_footprint", {"target": value, "max_queries": 3, "json_output": True}, "BRIGHTDATA_API_KEY"),
        ]

    if include_paid:
        return calls
    return [call for call in calls if call.optional_secret is None]
