import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "edge.py"
spec = importlib.util.spec_from_file_location("edge", MODULE_PATH)
assert spec and spec.loader
edge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(edge)


def test_public_prompt_routes_to_cloud() -> None:
    decision = edge.route_prompt("Summarize this public article", "gemini")
    assert decision.destination == "gemini"


def test_evidence_prompt_routes_to_xeon() -> None:
    decision = edge.route_prompt("Update the Beweismittel index", "gemini")
    assert decision.destination == "xeon"
