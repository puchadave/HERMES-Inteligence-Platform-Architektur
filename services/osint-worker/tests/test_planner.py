from app.planner import TargetKind, build_plan, classify_target, extract_target, normalize_target


def tool_names(target: str, *, include_paid: bool = False) -> list[str]:
    return [call.name for call in build_plan(target, include_paid=include_paid)]


def test_extracts_email_from_natural_language() -> None:
    assert extract_target("Prüfe bitte User.Test+osint@example.org auf Spuren") == "User.Test+osint@example.org"


def test_classifies_core_target_types() -> None:
    assert classify_target("person@example.org") is TargetKind.EMAIL
    assert classify_target("example.org") is TargetKind.DOMAIN
    assert classify_target("203.0.113.42") is TargetKind.IP
    assert classify_target("https://example.org/post/1") is TargetKind.URL
    assert classify_target("+49 170 1234567") is TargetKind.PHONE
    assert classify_target("example_handle") is TargetKind.USERNAME


def test_normalizes_domain_email_and_phone() -> None:
    assert normalize_target("EXAMPLE.ORG.", TargetKind.DOMAIN) == "example.org"
    assert normalize_target("User@EXAMPLE.ORG", TargetKind.EMAIL) == "user@example.org"
    assert normalize_target("+49 (170) 123-4567", TargetKind.PHONE) == "+491701234567"


def test_free_domain_plan_is_passive_and_keyless() -> None:
    assert tool_names("example.org") == [
        "search_whois",
        "search_dns",
        "search_domain",
        "search_github",
    ]


def test_paid_domain_plan_adds_optional_providers() -> None:
    assert tool_names("example.org", include_paid=True) == [
        "search_whois",
        "search_dns",
        "search_domain",
        "search_github",
        "search_virustotal",
        "search_censys",
        "search_shodan",
    ]


def test_plain_text_plan_avoids_paid_footprint_by_default() -> None:
    assert tool_names("Example Person") == ["search_github", "generate_dorks"]
