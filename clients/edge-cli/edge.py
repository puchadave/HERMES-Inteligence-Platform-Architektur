import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass

import httpx


SENSITIVE_MARKERS = (
    "beweismittel",
    "evidence",
    "fallakte",
    "private email",
    "roh-email",
    "zugangsdaten",
    "credential",
)


@dataclass(frozen=True)
class RouteDecision:
    destination: str
    reason: str


def route_prompt(prompt: str, preferred_cloud: str = "gemini") -> RouteDecision:
    lowered = prompt.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        return RouteDecision("xeon", "Sensitive or evidence-bound content remains on the Xeon core.")
    return RouteDecision(preferred_cloud, "Ordinary public task uses the configured direct cloud path.")


def call_gemini(prompt: str) -> str:
    api_key = os.environ["GEMINI_API_KEY"]
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    response = httpx.post(url, params={"key": api_key}, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=120)
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


def call_openai(prompt: str) -> str:
    api_key = os.environ["OPENAI_API_KEY"]
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    response = httpx.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "input": prompt},
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    if "output_text" in data:
        return data["output_text"]
    return json.dumps(data, ensure_ascii=False)


def call_xeon(prompt: str, profile: str) -> str:
    base_url = os.getenv("ODYSSEUS_API_URL", "http://api.localhost")
    token = os.getenv("ODYSSEUS_ACCESS_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = httpx.post(
        f"{base_url}/v1/search/dispatch",
        headers=headers,
        json={"query": prompt, "profile": profile},
        timeout=30,
        follow_redirects=True,
    )
    response.raise_for_status()
    return json.dumps(response.json(), indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Odysseus edge-first router")
    parser.add_argument("prompt", nargs="?", help="Task or question")
    parser.add_argument("--provider", choices=["auto", "gemini", "openai", "xeon"], default="auto")
    parser.add_argument("--profile", default="specialist")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    prompt = args.prompt or sys.stdin.read().strip()
    if not prompt:
        parser.error("A prompt is required.")

    preferred = os.getenv("ODYSSEUS_DEFAULT_CLOUD", "gemini")
    decision = RouteDecision(args.provider, "Provider explicitly selected.") if args.provider != "auto" else route_prompt(prompt, preferred)
    if args.dry_run:
        print(json.dumps(asdict(decision), ensure_ascii=False))
        return

    if decision.destination == "gemini":
        print(call_gemini(prompt))
    elif decision.destination == "openai":
        print(call_openai(prompt))
    else:
        print(call_xeon(prompt, args.profile))


if __name__ == "__main__":
    main()
