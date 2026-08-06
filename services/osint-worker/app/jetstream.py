from __future__ import annotations

from typing import Any


async def ensure_stream(
    jetstream: Any,
    *,
    name: str,
    subjects: tuple[str, ...],
) -> None:
    from nats.js.errors import BadRequestError, NotFoundError

    try:
        await jetstream.stream_info(name)
        return
    except NotFoundError:
        pass

    try:
        await jetstream.add_stream(name=name, subjects=list(subjects), storage="file")
    except BadRequestError:
        # Multiple services can race safely during cold start.
        await jetstream.stream_info(name)
