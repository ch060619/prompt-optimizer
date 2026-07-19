from __future__ import annotations

import json
from collections.abc import Iterator
from io import StringIO

from backend.rabbit_code.agent import AgentEvent, AgentEventType
from backend.rabbit_code.cli import EXIT_CANCELLED, EXIT_RUNTIME_ERROR, main
from typer.testing import CliRunner

from prompt_optimizer.cli.app import app

# RC ID: RC-069. Verify CLI command forms, stdin modes, snapshots, and stable exit codes.


class FakeRuntime:
    def __init__(self, events: list[AgentEvent]) -> None:
        self.events = events

    def stream(self, request: object) -> Iterator[AgentEvent]:
        yield from self.events


class TTYInput(StringIO):
    def isatty(self) -> bool:
        return True


runner = CliRunner()


def completed_runtime() -> FakeRuntime:
    return FakeRuntime(
        [
            AgentEvent(AgentEventType.STARTED),
            AgentEvent(AgentEventType.DELTA, text="完成"),
            AgentEvent(AgentEventType.COMPLETED),
        ]
    )


def test_rabbit_run_emits_jsonl_without_ansi() -> None:
    stdout = StringIO()
    stderr = StringIO()

    exit_code = main(
        ["run", "测试 JSONL", "--output", "jsonl"],
        stdout=stdout,
        stderr=stderr,
        runtime=completed_runtime(),
    )

    lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert exit_code == 0
    assert [line["type"] for line in lines] == ["started", "delta", "completed"]
    assert "\x1b[" not in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_one_shot_json_emits_a_single_snapshot() -> None:
    stdout = StringIO()

    exit_code = main(
        ["一次执行", "--output", "json"],
        stdout=stdout,
        runtime=completed_runtime(),
    )

    snapshot = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert [event["type"] for event in snapshot["events"]] == [
        "started",
        "delta",
        "completed",
    ]


def test_non_tty_stdin_is_consumed_as_a_single_prompt() -> None:
    stdout = StringIO()

    exit_code = main(
        ["--output", "text"],
        stdin=StringIO("来自管道"),
        stdout=stdout,
        runtime=completed_runtime(),
    )

    assert exit_code == 0
    assert stdout.getvalue() == "完成\n"


def test_tty_without_prompt_runs_interactively_without_machine_prompt() -> None:
    stdout = StringIO()

    exit_code = main(
        [],
        stdin=TTYInput("交互输入\n"),
        stdout=stdout,
        runtime=completed_runtime(),
    )

    assert exit_code == 0
    assert stdout.getvalue() == "rabbit> 完成\n"


def test_failed_and_cancelled_events_use_stable_exit_codes() -> None:
    failed_stderr = StringIO()
    failed = main(
        ["失败", "--output", "json"],
        stdout=StringIO(),
        stderr=failed_stderr,
        runtime=FakeRuntime([AgentEvent(AgentEventType.FAILED, text="failed")]),
    )
    cancelled = main(
        ["取消", "--output", "jsonl"],
        stdout=StringIO(),
        runtime=FakeRuntime([AgentEvent(AgentEventType.CANCELLED)]),
    )

    assert failed == EXIT_RUNTIME_ERROR
    assert cancelled == EXIT_CANCELLED
    assert "\x1b[" not in failed_stderr.getvalue()


def test_production_rabbit_run_command_uses_machine_output() -> None:
    result = runner.invoke(app, ["run", "生产入口", "--output", "json"])

    assert result.exit_code == 0
    assert [event["type"] for event in json.loads(result.stdout)["events"]][-1] == "completed"
    assert "\x1b[" not in result.stdout
