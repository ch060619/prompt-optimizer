from __future__ import annotations

from collections.abc import Iterator
from io import StringIO

from backend.rabbit_code.agent import AgentEvent, AgentEventType
from backend.rabbit_code.cli import main
from backend.rabbit_code.tui import TuiRenderer, TuiSession, TuiState

# RC ID: RC-101. Verify event-driven TUI state, narrow layout, and CLI entrypoint.


class FakeRuntime:
    def stream(self, request: object) -> Iterator[AgentEvent]:
        yield AgentEvent(AgentEventType.STARTED)
        yield AgentEvent(
            AgentEventType.TOOL_CARD,
            payload={"tool": "read_file", "status": "running", "plan": ["inspect"]},
        )
        yield AgentEvent(
            AgentEventType.WARNING,
            payload={
                "permission_required": True,
                "approval": "workspace read",
                "approval_request": {
                    "approval_id": "approval-1",
                    "request_id": "request-1",
                    "action": "terminal.exec",
                    "description": "Run a local command",
                    "risk": "high",
                    "tool": "terminal.exec",
                    "command": ["python", "-c", "print(1)"],
                    "paths": ["C:/workspace/output.txt"],
                    "workdir": "C:/workspace",
                    "impact": "starts one local process",
                    "authorization_scope": "once",
                    "arguments": {"command": ["python", "-c", "print(1)"]},
                    "snapshot": "snapshot",
                    "expires_at": None,
                },
                "usage": {"output_tokens": 3, "cost": 0},
            },
        )
        yield AgentEvent(AgentEventType.DELTA, text="streamed result")
        yield AgentEvent(AgentEventType.COMPLETED)


def test_tui_consumes_shared_events_and_keeps_state_sections() -> None:
    state = TuiSession(FakeRuntime()).submit("show status")

    assert state.output == ["streamed result"]
    assert state.tool_status == "read_file: running"
    assert state.plan == ["inspect"]
    assert state.usage == {"output_tokens": 3, "cost": 0}
    assert state.permission_prompt is None
    rendered = TuiRenderer.render(state, width=40, height=10)
    assert "Rabbit Code" in rendered
    assert "streamed result" in rendered
    assert "Usage:" in rendered
    assert "\x1b[" not in rendered
    assert all(len(line) <= 40 for line in rendered.splitlines())


def test_tui_renders_permission_diff_and_long_text_without_overflow() -> None:
    state = TuiState(
        prompt="a very long prompt that must be clipped",
        output=["long output " * 20],
        permission_prompt="confirm write",
        plan=["one", "two"],
        diff="-old\n+new",
        usage={"cost": 1},
        status="running",
    )
    rendered = TuiRenderer.render(state, width=32, height=12)

    assert "Approval: confirm write" in rendered
    assert "Plan:" in rendered
    assert "Diff:" in rendered
    assert all(len(line) <= 32 for line in rendered.splitlines())


def test_tui_keeps_the_shared_approval_request_while_waiting() -> None:
    state = TuiState()
    state.apply(
        AgentEvent(
            AgentEventType.WARNING,
            payload={
                "approval_required": True,
                "approval_request": {
                    "approval_id": "approval-2",
                    "request_id": "request-2",
                    "action": "files.delete",
                    "description": "Delete one file",
                    "risk": "high",
                    "tool": "files.delete",
                    "command": ["delete"],
                    "paths": ["C:/workspace/secret.txt"],
                    "workdir": "C:/workspace",
                    "impact": "deletes one workspace file",
                    "authorization_scope": "once",
                    "arguments": {"path": "secret.txt"},
                    "snapshot": "snapshot",
                    "expires_at": None,
                },
            },
        )
    )

    assert state.approval_request is not None
    assert state.approval_request.tool == "files.delete"
    assert "Command: delete" in TuiRenderer.render(state, width=40, height=12)


def test_tui_cli_entrypoint_is_machine_stable(tmp_path) -> None:  # type: ignore[no-untyped-def]
    del tmp_path
    stdout = StringIO()
    result = main(
        ["tui", "hello", "--width", "40", "--height", "10"],
        stdout=stdout,
        stderr=StringIO(),
        runtime=FakeRuntime(),
    )

    assert result == 0
    assert "Rabbit Code" in stdout.getvalue()
