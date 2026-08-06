from app.models import DataClass, Route
from app.policy import PolicyEngine


def test_standard_profile_stays_in_searxng() -> None:
    decision = PolicyEngine().decide("standard", "current public news")
    assert decision.route == Route.SEARXNG
    assert decision.data_class == DataClass.PUBLIC


def test_specialist_profile_routes_to_xeon() -> None:
    decision = PolicyEngine().decide("specialist", "correlate supplied case artifacts")
    assert decision.route == Route.XEON_QUEUE
    assert decision.data_class == DataClass.EVIDENCE


def test_evidence_marker_overrides_public_profile() -> None:
    decision = PolicyEngine().decide("social", "update the Beweismittel timeline")
    assert decision.route == Route.XEON_QUEUE
    assert decision.data_class == DataClass.EVIDENCE


def test_unknown_profile_is_contained() -> None:
    decision = PolicyEngine().decide("unregistered", "test")
    assert decision.profile == "specialist"
    assert decision.route == Route.XEON_QUEUE
