import html
import uuid
from functools import lru_cache

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from .models import JobAccepted, Route, SearchDecision, SearchRequest
from .policy import PolicyEngine
from .queue import NatsPublisher
from .settings import get_settings

app = FastAPI(title="Odysseus API", version="0.2.0")


@lru_cache
def get_policy() -> PolicyEngine:
    return PolicyEngine.from_yaml(get_settings().search_profiles_path)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "odysseus-api"}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(
        "odysseus_api_up 1\n",
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.post("/v1/classify", response_model=SearchDecision)
async def classify(request: SearchRequest) -> SearchDecision:
    return get_policy().decide(request.profile, request.query)


@app.post("/v1/search/dispatch", response_model=JobAccepted)
async def dispatch(
    request: SearchRequest,
    x_auth_request_user: str | None = Header(default=None),
) -> JobAccepted:
    decision = get_policy().decide(request.profile, request.query)
    if decision.route == Route.SEARXNG:
        raise HTTPException(status_code=409, detail="Standard searches must remain in SearXNG.")

    settings = get_settings()
    job_id = str(uuid.uuid4())
    payload = {
        "job_id": job_id,
        "query": request.query,
        "profile": request.profile,
        "requested_by": x_auth_request_user or request.requested_by or "unknown",
        "metadata": request.metadata,
        "decision": decision.model_dump(mode="json"),
    }
    publisher = NatsPublisher(
        settings.nats_url,
        stream=settings.nats_stream,
        subjects=(settings.nats_subject, settings.nats_result_subject),
    )
    try:
        await publisher.publish(settings.nats_subject, payload)
        status = "queued"
    except Exception:
        status = "deferred"

    return JobAccepted(job_id=job_id, status=status, subject=settings.nats_subject, decision=decision)


@app.get("/ui/search", response_class=HTMLResponse)
async def search_ui(
    request: Request,
    q: str = Query(min_length=2, max_length=4000),
    profile: str = Query(default="specialist"),
    x_auth_request_user: str | None = Header(default=None),
) -> HTMLResponse:
    accepted = await dispatch(
        SearchRequest(query=q, profile=profile),
        x_auth_request_user=x_auth_request_user,
    )
    safe_query = html.escape(q)
    safe_profile = html.escape(profile)
    safe_user = html.escape(x_auth_request_user or "unknown")
    body = f"""
<!doctype html>
<html lang="de"><head><meta charset="utf-8"><title>Odysseus Dispatch</title>
<style>body{{font-family:system-ui;max-width:920px;margin:3rem auto;padding:0 1rem}}code{{background:#eee;padding:.2rem .4rem}}.card{{border:1px solid #bbb;border-radius:.6rem;padding:1rem;margin:1rem 0}}</style>
</head><body>
<h1>Odysseus Specialist Dispatch</h1>
<div class="card"><strong>Query:</strong> {safe_query}<br><strong>Profile:</strong> {safe_profile}<br><strong>User:</strong> {safe_user}</div>
<div class="card"><strong>Job:</strong> <code>{accepted.job_id}</code><br><strong>Status:</strong> {accepted.status}<br><strong>Route:</strong> {accepted.decision.route}<br><strong>Data class:</strong> {accepted.decision.data_class}</div>
<p><a href="/">Back to SearXNG</a></p>
</body></html>"""
    return HTMLResponse(body)
