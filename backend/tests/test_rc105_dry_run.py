from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from backend.rabbit_code.cli import EXIT_OK, EXIT_USAGE_ERROR, main
from backend.rabbit_code.dry_run import (
    DryRunPlanner,
    MachineEventStream,
    MachineEventType,
)

# RC ID: RC-105. Verify dry-run plans, read-only behavior, machine events, and log levels.


def test_dry_run_planner_never_marks_actions_executable(tmp_path: Path) -> None:
    action = DryRunPlanner().plan(("rabbit", "run", "prompt"), cwd=tmp_path)

    assert not action.would_execute
    assert action.permission == "read-only"
    assert action.cwd == tmp_path.resolve()


def test_machine_event_stream_has_stable_sequences_and_jsonl() -> None:
    stream = MachineEventStream()
    stream.emit(MachineEventType.STARTED, {"mode": "dry-run"})
    stream.emit(MachineEventType.COMPLETED)

    payload = [json.loads(line) for line in stream.jsonl().splitlines()]
    assert [item["seq"] for item in payload] == [0, 1]
    assert stream.json()["events"] == payload


def test_cli_dry_run_is_machine_readable_and_conflicts_are_usage_errors() -> None:
    stdout = StringIO()
    result = main(
        ["--dry-run", "--output", "json", "hello", "--log-level", "debug"],
        stdin=StringIO(""),
        stdout=stdout,
        stderr=StringIO(),
    )
    payload = json.loads(stdout.getvalue())
    assert result == EXIT_OK
    assert payload["events"][0]["type"] == "dry_run"
    assert not payload["events"][0]["payload"]["action"]["would_execute"]
    assert payload["events"][0]["payload"]["log_level"] == "debug"

    assert (
        main(
            ["--dry-run", "--read-only", "--permission-policy", "approve", "hello"],
            stdout=StringIO(),
            stderr=StringIO(),
        )
        == EXIT_USAGE_ERROR
    )
