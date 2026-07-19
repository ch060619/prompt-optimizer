from __future__ import annotations

import json
from collections.abc import Iterator
from io import StringIO

from backend.rabbit_code.agent import AgentEvent, AgentEventType
from backend.rabbit_code.cli import EXIT_OK, EXIT_USAGE_ERROR, main

# RC ID: RC-100. Verify command forms, generated options, and stable control output.


class FakeRuntime:
    def stream(self, request: object) -> Iterator[AgentEvent]:
        yield AgentEvent(AgentEventType.STARTED)
        yield AgentEvent(AgentEventType.DELTA, text="done")
        yield AgentEvent(AgentEventType.COMPLETED)


def test_continue_and_resume_require_session_and_accept_machine_options() -> None:
    stdout = StringIO()
    assert (
        main(
            [
                "continue",
                "session-1",
                "continue prompt",
                "--output",
                "json",
                "--model",
                "offline",
                "--mode",
                "plan",
            ],
            stdout=stdout,
            stderr=StringIO(),
            runtime=FakeRuntime(),
        )
        == EXIT_OK
    )
    assert json.loads(stdout.getvalue())["events"][-1]["type"] == "completed"
    assert (
        main(
            ["resume", "session-2", "resume prompt", "--output", "jsonl"],
            stdout=StringIO(),
            stderr=StringIO(),
            runtime=FakeRuntime(),
        )
        == EXIT_OK
    )
    error = StringIO()
    assert (
        main(["continue"], stdout=StringIO(), stderr=error, runtime=FakeRuntime())
        == EXIT_USAGE_ERROR
    )
    assert "session id" in error.getvalue()


def test_model_mode_and_output_control_commands_are_machine_readable() -> None:
    for command, value in (("model", "offline"), ("mode", "edit"), ("output", "json")):
        stdout = StringIO()
        assert (
            main([command, value, "--output", "json"], stdout=stdout, stderr=StringIO())
            == EXIT_OK
        )
        assert json.loads(stdout.getvalue()) == {"command": command, "value": value}

    error = StringIO()
    assert main(["mode", "unsafe"], stdout=StringIO(), stderr=error) == EXIT_USAGE_ERROR
    assert "mode must be" in error.getvalue()


def test_legacy_prompt_and_stdin_forms_remain_supported() -> None:
    stdout = StringIO()
    assert (
        main(
            ["legacy prompt", "--output", "text"],
            stdout=stdout,
            stderr=StringIO(),
            runtime=FakeRuntime(),
        )
        == EXIT_OK
    )
    assert stdout.getvalue() == "done\n"
