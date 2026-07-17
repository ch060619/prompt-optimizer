from __future__ import annotations

import httpx
from backend.rabbit_code.agent import AgentEventType
from backend.rabbit_code.runtime import AppServerRuntime, InProcessRuntime

from prompt_optimizer.providers.base import (
    ModelRequest,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
)

# RC ID: RC-059. Verify in-process and App Server runtimes share Agent events.


class FakeProvider:
    name = "fake"
    capabilities = ProviderCapabilities(streaming=True)

    def optimize(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        raise AssertionError("runtime stream should not call optimize")

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        yield ProviderEvent(ProviderEventType.STARTED)
        yield ProviderEvent(ProviderEventType.DELTA, text="统一")
        yield ProviderEvent(ProviderEventType.DELTA, text="事件")
        yield ProviderEvent(ProviderEventType.COMPLETED)


def test_in_process_and_app_server_runtime_have_the_same_event_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Rabbit-Code-Startup-Token"] == "runtime-token"
        assert request.headers["X-Rabbit-Code-Protocol"] == "v1"
        return httpx.Response(
            200,
            content=(
                'event: started\ndata: {"type":"started"}\n\n'
                'event: delta\ndata: {"type":"delta","text":"统一"}\n\n'
                'event: delta\ndata: {"type":"delta","text":"事件"}\n\n'
                'event: completed\ndata: {"type":"completed"}\n\n'
            ),
        )

    request = ModelRequest(prompt="测试 runtime")
    in_process = list(InProcessRuntime(FakeProvider()).stream(request))
    app_server = list(
        AppServerRuntime(
            "https://example.test",
            "runtime-token",
            client=httpx.Client(transport=httpx.MockTransport(handler)),
        ).stream(request)
    )

    assert [event.type for event in in_process] == [
        AgentEventType.STARTED,
        AgentEventType.DELTA,
        AgentEventType.DELTA,
        AgentEventType.COMPLETED,
    ]
    assert [(event.type, event.text) for event in app_server] == [
        (event.type, event.text) for event in in_process
    ]
