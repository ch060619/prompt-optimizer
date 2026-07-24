from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Iterator
from io import StringIO
from pathlib import Path

import pytest
from backend.rabbit_code.agent import AgentEvent, AgentEventType
from backend.rabbit_code.ci_execution import PermissionStrategy, resolve_non_interactive_policy
from backend.rabbit_code.cli import (
    EXIT_CANCELLED,
    EXIT_PERMISSION_DENIED,
    EXIT_RUNTIME_ERROR,
    EXIT_USAGE_ERROR,
    main,
)
from backend.rabbit_code.terminal_compatibility import TerminalKind, detect_terminal_matrix

# RC ID: RC-233. Exercise CLI surfaces without real Provider or model resources.


class FakeRuntime:
    def __init__(
        self,
        events: tuple[AgentEvent, ...],
        *,
        error: BaseException | None = None,
    ) -> None:
        self.events = events
        self.error = error

    def stream(self, request: object) -> Iterator[AgentEvent]:
        if self.error is not None:
            raise self.error
        yield from self.events


class TTYInput(StringIO):
    def isatty(self) -> bool:
        return True


def _completed_runtime() -> FakeRuntime:
    return FakeRuntime(
        (
            AgentEvent(AgentEventType.STARTED),
            AgentEvent(AgentEventType.DELTA, text="done"),
            AgentEvent(AgentEventType.COMPLETED),
        )
    )


@pytest.mark.parametrize("mode", ("text", "json", "jsonl"))
def test_cli_output_modes_are_stable_and_machine_safe(mode: str) -> None:
    stdout = StringIO()
    exit_code = main(
        ["run", "prompt", "--output", mode],
        stdout=stdout,
        stderr=StringIO(),
        runtime=_completed_runtime(),
    )

    assert exit_code == 0
    assert "\x1b[" not in stdout.getvalue()
    if mode == "text":
        assert stdout.getvalue() == "done\n"
    elif mode == "json":
        assert json.loads(stdout.getvalue())["events"][-1]["type"] == "completed"
    else:
        assert [json.loads(line)["type"] for line in stdout.getvalue().splitlines()] == [
            "started",
            "delta",
            "completed",
        ]


def test_cli_tty_prompts_once_and_non_tty_reads_stdin_without_prompt() -> None:
    interactive_stdout = StringIO()
    assert (
        main(
            [],
            stdin=TTYInput("interactive prompt\n"),
            stdout=interactive_stdout,
            stderr=StringIO(),
            runtime=_completed_runtime(),
        )
        == 0
    )
    assert interactive_stdout.getvalue() == "rabbit> done\n"

    piped_stdout = StringIO()
    assert (
        main(
            ["--output", "jsonl"],
            stdin=StringIO("piped prompt"),
            stdout=piped_stdout,
            stderr=StringIO(),
            runtime=_completed_runtime(),
        )
        == 0
    )
    assert "rabbit>" not in piped_stdout.getvalue()
    assert json.loads(piped_stdout.getvalue().splitlines()[0])["type"] == "started"


def test_cli_noninteractive_policy_and_permission_exit_codes_are_explicit() -> None:
    policy = resolve_non_interactive_policy(
        stdin_is_tty=False,
        force_non_interactive=True,
        requested="read-only",
    )
    assert policy is not None
    assert policy.strategy is PermissionStrategy.READ_ONLY

    missing_policy = StringIO()
    assert (
        main(
            ["--non-interactive"],
            stdin=StringIO(),
            stdout=StringIO(),
            stderr=missing_policy,
            runtime=_completed_runtime(),
        )
        == EXIT_USAGE_ERROR
    )
    assert "permission-policy" in missing_policy.getvalue()

    denied_stderr = StringIO()
    denied = main(
        ["--non-interactive", "--permission-policy", "deny", "prompt"],
        stdout=StringIO(),
        stderr=denied_stderr,
        runtime=FakeRuntime((), error=PermissionError("approval required")),
    )
    assert denied == EXIT_PERMISSION_DENIED
    assert "permission denied" in denied_stderr.getvalue()


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (RuntimeError("runtime"), EXIT_RUNTIME_ERROR),
        (KeyboardInterrupt(), EXIT_CANCELLED),
    ],
)
def test_cli_runtime_and_cancel_exit_codes_are_stable(
    error: BaseException,
    expected: int,
) -> None:
    stderr = StringIO()
    assert (
        main(
            ["prompt", "--output", "json"],
            stdout=StringIO(),
            stderr=stderr,
            runtime=FakeRuntime((), error=error),
        )
        == expected
    )
    assert "\x1b[" not in stderr.getvalue()


def test_continue_and_resume_preserve_session_arguments_in_machine_output() -> None:
    for command, args in (
        ("continue", ["continue", "session-1", "continue prompt"]),
        ("resume", ["resume", "--session", "session-2", "resume prompt"]),
    ):
        stdout = StringIO()
        assert (
            main(
                [*args, "--output", "json"],
                stdout=stdout,
                stderr=StringIO(),
                runtime=_completed_runtime(),
            )
            == 0
        )
        snapshot = json.loads(stdout.getvalue())
        assert snapshot["events"][-1]["type"] == "completed"
        assert command in {"continue", "resume"}

    error = StringIO()
    assert (
        main(
            ["resume"],
            stdout=StringIO(),
            stderr=error,
            runtime=_completed_runtime(),
        )
        == EXIT_USAGE_ERROR
    )
    assert "session id" in error.getvalue()


def test_cli_dry_run_json_is_a_single_safe_machine_snapshot() -> None:
    stdout = StringIO()
    assert (
        main(
            ["run", "dry run", "--dry-run", "--output", "json", "--read-only"],
            stdout=stdout,
            stderr=StringIO(),
            runtime=_completed_runtime(),
        )
        == 0
    )
    snapshot = json.loads(stdout.getvalue())
    assert snapshot["events"][0]["type"] == "dry_run"
    assert snapshot["events"][0]["payload"]["action"]["permission"] == "read-only"


def test_terminal_shell_matrix_reports_unavailable_linux_explicitly_on_windows() -> None:
    matrix = {item.kind: item for item in detect_terminal_matrix()}
    assert set(matrix) == set(TerminalKind)
    if sys.platform == "win32" and not matrix[TerminalKind.LINUX].available:
        assert "Windows host" in matrix[TerminalKind.LINUX].reason


def test_cli_subprocess_jsonl_has_no_prompt_or_ansi_pollution() -> None:
    env = os.environ.copy()
    backend_src = str(Path.cwd() / "backend" / "src")
    env["PYTHONPATH"] = os.pathsep.join(
        item for item in (backend_src, env.get("PYTHONPATH")) if item
    )
    result = subprocess.run(
        [sys.executable, "-m", "backend.rabbit_code.cli", "run", "--output", "jsonl"],
        input="subprocess prompt\n",
        text=True,
        capture_output=True,
        check=False,
        env=env,
        timeout=20,
    )

    assert result.returncode == 0
    assert "rabbit>" not in result.stdout
    assert "\x1b[" not in result.stdout
    assert json.loads(result.stdout.splitlines()[-1])["type"] == "completed"
