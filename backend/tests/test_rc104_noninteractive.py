from __future__ import annotations

from collections.abc import Iterator
from io import StringIO

from backend.rabbit_code.agent import AgentEvent, AgentEventType
from backend.rabbit_code.ci_execution import (
    PermissionStrategy,
    resolve_non_interactive_policy,
)
from backend.rabbit_code.cli import EXIT_PERMISSION_DENIED, EXIT_USAGE_ERROR, main

# RC ID: RC-104. Verify no-TTY policy, no prompt wait, stable output, and denial exit code.


class FakeRuntime:
    def __init__(self, *, permission_denied: bool = False) -> None:
        self.permission_denied = permission_denied

    def stream(self, request: object) -> Iterator[AgentEvent]:
        if self.permission_denied:
            raise PermissionError("dangerous action requires approval")
        yield AgentEvent(AgentEventType.STARTED)
        yield AgentEvent(AgentEventType.COMPLETED)


def test_noninteractive_requires_policy_only_when_explicitly_requested() -> None:
    with_policy = resolve_non_interactive_policy(
        stdin_is_tty=False,
        force_non_interactive=True,
        requested="read-only",
    )
    assert with_policy is not None
    assert with_policy.strategy is PermissionStrategy.READ_ONLY
    assert with_policy.explicit
    compatibility = resolve_non_interactive_policy(
        stdin_is_tty=False,
        force_non_interactive=False,
        requested=None,
    )
    assert compatibility is not None
    assert compatibility.strategy is PermissionStrategy.READ_ONLY


def test_noninteractive_missing_policy_fails_without_waiting_for_input() -> None:
    stderr = StringIO()
    result = main(
        ["--non-interactive"],
        stdin=StringIO(""),
        stdout=StringIO(),
        stderr=stderr,
        runtime=FakeRuntime(),
    )

    assert result == EXIT_USAGE_ERROR
    assert "permission-policy" in stderr.getvalue()


def test_noninteractive_read_only_is_machine_stable_and_denial_has_dedicated_code() -> None:
    stdout = StringIO()
    result = main(
        ["--non-interactive", "--permission-policy", "read-only", "prompt", "--output", "json"],
        stdin=StringIO(""),
        stdout=stdout,
        stderr=StringIO(),
        runtime=FakeRuntime(),
    )
    assert result == 0
    assert '"events"' in stdout.getvalue()

    stderr = StringIO()
    denied = main(
        ["--non-interactive", "--permission-policy", "deny", "prompt"],
        stdout=StringIO(),
        stderr=stderr,
        runtime=FakeRuntime(permission_denied=True),
    )
    assert denied == EXIT_PERMISSION_DENIED
    assert "permission denied" in stderr.getvalue()
