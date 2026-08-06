from __future__ import annotations

import re
from typing import Any

from .mcp_client import MCPClient
from .reporting import normalize_tool_result

_GITHUB_REPOSITORY = re.compile(
    r"https?://(?:www\.)?github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)


def parse_github_repository(value: str) -> tuple[str, str] | None:
    match = _GITHUB_REPOSITORY.search(value)
    if not match:
        return None
    repo = match.group("repo").removesuffix(".git")
    return match.group("owner"), repo


async def collect_repository_context(
    value: str,
    *,
    mcp_url: str,
    token: str,
) -> dict[str, Any] | None:
    repository = parse_github_repository(value)
    if repository is None or not token:
        return None

    owner, repo = repository
    headers = {"Authorization": f"Bearer {token}"}
    async with MCPClient(mcp_url, headers=headers, timeout_seconds=120) as client:
        tools = await client.list_tools()
        available = {str(tool.get("name")) for tool in tools if tool.get("name")}
        if "get_file_contents" not in available:
            return {
                "status": "unavailable",
                "owner": owner,
                "repo": repo,
                "error": "GitHub MCP did not expose get_file_contents",
            }
        result = await client.call_tool(
            "get_file_contents",
            {"owner": owner, "repo": repo, "path": "/"},
        )
        return {
            "status": "ok",
            "owner": owner,
            "repo": repo,
            "root": normalize_tool_result(result),
        }
