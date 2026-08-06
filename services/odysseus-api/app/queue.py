import json
from typing import Any


class NatsPublisher:
    def __init__(
        self,
        url: str,
        *,
        stream: str = "ODYSSEUS_SEARCH",
        subjects: tuple[str, ...] = ("odysseus.jobs.search", "odysseus.results.search"),
    ) -> None:
        self.url = url
        self.stream = stream
        self.subjects = subjects

    async def publish(self, subject: str, payload: dict[str, Any]) -> None:
        import nats
        from nats.js.errors import BadRequestError, NotFoundError

        client = await nats.connect(self.url, connect_timeout=2, max_reconnect_attempts=2)
        try:
            jetstream = client.jetstream(timeout=3)
            try:
                await jetstream.stream_info(self.stream)
            except NotFoundError:
                try:
                    await jetstream.add_stream(name=self.stream, subjects=list(self.subjects), storage="file")
                except BadRequestError:
                    # Another publisher may have created the stream concurrently.
                    await jetstream.stream_info(self.stream)
            await jetstream.publish(
                subject,
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                timeout=3,
                stream=self.stream,
            )
        finally:
            await client.close()
