from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class DataClass(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    EVIDENCE = "evidence"


class Route(StrEnum):
    SEARXNG = "searxng"
    CLOUD_DIRECT = "cloud_direct"
    XEON_QUEUE = "xeon_queue"


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    profile: str = "standard"
    requested_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchDecision(BaseModel):
    profile: str
    route: Route
    data_class: DataClass
    reason: str


class JobAccepted(BaseModel):
    job_id: str
    status: str
    subject: str
    decision: SearchDecision
