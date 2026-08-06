import json
from typing import Any


class NatsPublisher:
    def __init__(self, url: str) -> None:
        self.url = url

    async def publish(self, subject: str, payload: dict[str, Any]) -> None:
        import nats

        client = await nats.connect(self.url, connect_timeout=2, max_reconnect_attempts=2)
        try:
            await client.publish(subject, json.dumps(payload, ensure_ascii=False).encode("utf-8"))
            await client.flush(timeout=2)
        finally:
            await client.close()
