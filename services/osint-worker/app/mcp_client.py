from __future__ import annotations

import json
from itertools import count
from typing import Any

import httpx


class MCPError(RuntimeError):
    pass


class MCPClient:
    def __init__(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout_seconds: float = 180.0,
    ) -> None:
        self.url = url
        self.headers = headers or {}
        self.timeout_seconds = timeout_seconds
        self.session_id: str | None = None
        self._ids = count(1)
        self._initialized = False

    async def __aenter__(self) -> "MCPClient":
        await self.initialize()
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def initialize(self) -> dict[str, Any]:
        if self._initialized:
            return {}
        result = await self._request(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "odysseus-osint-worker", "version": "0.2.0"},
            },
        )
        await self._notify("notifications/initialized", {})
        self._initialized = True
        return result

    async def list_tools(self) -> list[dict[str, Any]]:
        await self.initialize()
        result = await self._request("tools/list", {})
        return list(result.get("tools", []))

    async def call_tool(self, name: str, arguments: dict[str, object]) -> dict[str, Any]:
        await self.initialize()
        return await self._request("tools/call", {"name": name, "arguments": arguments})

    async def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = next(self._ids)
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        message = await self._post(payload)
        if message.get("id") != request_id:
            raise MCPError(f"MCP response id mismatch for {method}")
        if "error" in message:
            raise MCPError(f"MCP {method} failed: {message['error']}")
        result = message.get("result")
        return result if isinstance(result, dict) else {"value": result}

    async def _notify(self, method: str, params: dict[str, Any]) -> None:
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        await self._post(payload, notification=True)

    async def _post(self, payload: dict[str, Any], *, notification: bool = False) -> dict[str, Any]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            **self.headers,
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = await client.post(self.url, headers=headers, json=payload)

        if response.status_code >= 400:
            raise MCPError(f"MCP HTTP {response.status_code}: {response.text[:500]}")

        returned_session = response.headers.get("mcp-session-id")
        if returned_session:
            self.session_id = returned_session

        if notification or response.status_code == 202 or not response.content:
            return {}

        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            messages: list[dict[str, Any]] = []
            for line in response.text.splitlines():
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if not raw or raw == "[DONE]":
                    continue
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    messages.append(parsed)
            if not messages:
                raise MCPError("MCP stream contained no JSON-RPC message")
            return messages[-1]

        try:
            parsed = response.json()
        except ValueError as exc:
            raise MCPError("MCP returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise MCPError("MCP response must be a JSON object")
        return parsed
