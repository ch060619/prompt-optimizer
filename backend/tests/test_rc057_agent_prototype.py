from __future__ import annotations

import json
from pathlib import Path
from threading import Event

from backend.rabbit_code.agent import AgentCore, AgentEventType
from backend.rabbit_code.cli import run
from backend.rabbit_code.prototype_app import create_app
from fastapi.testclient import TestClient

from prompt_optimizer.providers.base import (
    ModelRequest,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
)

# RC ID: RC-057. Verify the candidate Python Agent Core event and cancellation boundary.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class FakeProvider:
    name = "fake"
    capabilities = ProviderCapabilities(streaming=True)

    def optimize(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        raise AssertionError("prototype stream should not call optimize")

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        yield ProviderEvent(ProviderEventType.STARTED)
        yield ProviderEvent(ProviderEventType.DELTA, text="第一段")
        yield ProviderEvent(ProviderEventType.DELTA, text="第二段")
        yield ProviderEvent(ProviderEventType.COMPLETED)


def test_agent_core_maps_provider_events_without_changing_provider_contract() -> None:
    events = list(AgentCore(FakeProvider()).stream(ModelRequest(prompt="测试")))

    assert [event.type for event in events] == [
        AgentEventType.STARTED,
        AgentEventType.DELTA,
        AgentEventType.DELTA,
        AgentEventType.COMPLETED,
    ]
    assert "".join(event.text or "" for event in events[1:-1]) == "第一段第二段"


def test_agent_core_emits_cancelled_and_stops_before_completed() -> None:
    cancellation = Event()
    cancellation.set()

    events = list(
        AgentCore(FakeProvider()).stream(
            ModelRequest(prompt="测试"),
            cancellation=cancellation,
        )
    )

    assert [event.type for event in events] == [AgentEventType.STARTED, AgentEventType.CANCELLED]


def test_prototype_app_and_cli_share_the_agent_event_sequence() -> None:
    app_events = []
    with TestClient(create_app(FakeProvider())) as client:
        response = client.post("/agent/stream", json={"prompt": "测试"})
        app_events = [line for line in response.text.splitlines() if line.startswith("event: ")]

    cli_events = [event.type.value for event in run("测试")]

    assert app_events == [
        "event: started",
        "event: delta",
        "event: delta",
        "event: completed",
    ]
    assert cli_events[0] == AgentEventType.STARTED.value
    assert cli_events[-1] == AgentEventType.COMPLETED.value


def test_candidate_adr_records_unverified_platform_boundaries() -> None:
    adr = (REPOSITORY_ROOT / "docs" / "adr" / "0006-candidate-architecture-baseline.md").read_text(
        encoding="utf-8"
    )
    benchmark = json.loads(
        (REPOSITORY_ROOT / "docs" / "benchmarks" / "rc-057-windows.json").read_text(
            encoding="utf-8"
        )
    )

    assert "Status: Proposed" in adr
    assert benchmark["prototype_app_server"]["ready"] is True
    assert benchmark["linux"]["status"] == "not_run"
    assert benchmark["tauri"]["status"] == "not_built"
    assert benchmark["typescript_alternative"]["status"] == "not_built"
