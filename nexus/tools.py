from dataclasses import dataclass
from typing import Awaitable, Callable

import httpx

from nexus.config import settings


ToolHandler = Callable[[dict], Awaitable[dict]]


@dataclass(frozen=True)
class Tool:
    name: str
    scope: str
    handler: ToolHandler


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools)


async def github_repo(args: dict) -> dict:
    repo = args["repository"]
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"https://api.github.com/repos/{repo}", headers=headers)
        response.raise_for_status()
        data = response.json()
    return {
        "full_name": data["full_name"],
        "default_branch": data["default_branch"],
        "open_issues": data["open_issues_count"],
        "updated_at": data["updated_at"],
    }


registry = ToolRegistry()
registry.register(Tool("github.repo.read", "READ", github_repo))
