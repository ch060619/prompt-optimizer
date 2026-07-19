from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Protocol

import httpx

from prompt_optimizer.contracts import Provider
from prompt_optimizer.providers.base import ModelRequest
from prompt_optimizer.providers.offline import OfflineRuleProvider

from .agent import AgentCore, AgentEvent, AgentEventType

# RC ID: RC-059. Share one event model between in-process and App Server runtimes.


class AgentRuntime(Protocol):
    def stream(self, request: ModelRequest) -> Iterator[AgentEvent]:
        pass


class InProcessRuntime:
    def __init__(self, provider: Provider | None = None) -> None:
        self.core = AgentCore(provider or OfflineRuleProvider())

    def stream(self, request: ModelRequest) -> Iterator[AgentEvent]:
        yield from self.core.stream(request)


class AppServerRuntime:
    def __init__(
        self,
        base_url: str,
        startup_token: str,
        protocol_version: str = "v1",
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.startup_token = startup_token
        self.protocol_version = protocol_version
        self.client = client or httpx.Client()

    def stream(self, request: ModelRequest) -> Iterator[AgentEvent]:
        with self.client.stream(
            "POST",
            f"{self.base_url}/agent/stream",
            headers={
                "Content-Type": "application/json",
                "X-Rabbit-Code-Startup-Token": self.startup_token,
                "X-Rabbit-Code-Protocol": self.protocol_version,
            },
            json={"prompt": request.prompt},
        ) as response:
            response.raise_for_status()
            yield from _parse_sse(response.iter_lines())


def _parse_sse(lines: Iterator[str]) -> Iterator[AgentEvent]:
    event_name: str | None = None
    data: str | None = None
    for line in lines:
        if line.startswith("event: "):
            event_name = line.removeprefix("event: ")
        elif line.startswith("data: "):
            data = line.removeprefix("data: ")
        elif not line and event_name and data:
            payload = json.loads(data)
            event_type = AgentEventType(event_name)
            yield AgentEvent(
                event_type,
                payload.get("text"),
                int(payload.get("seq", 0)),
                payload.get("payload", {}),
            )
            event_name = None
            data = None
