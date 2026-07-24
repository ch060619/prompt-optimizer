from __future__ import annotations

from backend.rabbit_code.agent import AgentEvent, AgentEventType

# RC ID: RC-245. Verify event ordering, resume serialization, and safe unknown-event fallback.


def test_agent_events_round_trip_for_cli_resume_and_gui_rendering() -> None:
    source = [
        AgentEvent(AgentEventType.STARTED, sequence=0),
        AgentEvent(
            AgentEventType.TOOL_CARD,
            text="read file",
            sequence=1,
            payload={"path": "a.py"},
        ),
        AgentEvent(AgentEventType.DELTA, text="result", sequence=2),
        AgentEvent(AgentEventType.COMPLETED, sequence=3),
    ]

    resumed = [AgentEvent.from_dict(event.to_dict()) for event in source]

    assert resumed == source
    assert [event.sequence for event in resumed] == [0, 1, 2, 3]


def test_unknown_event_is_renderable_without_breaking_resume() -> None:
    event = AgentEvent.from_dict(
        {
            "type": "future.tool.progress",
            "seq": 7,
            "text": "still working",
            "payload": {"percent": 50},
        }
    )

    assert event.type is AgentEventType.TERMINAL
    assert event.sequence == 7
    assert event.text == "still working"
    assert event.payload["unknown_event_type"] == "future.tool.progress"
    assert event.payload["original_payload"] == {"percent": 50}
