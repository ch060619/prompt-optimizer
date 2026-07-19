from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.local_model_state import (
    LocalModelState,
    LocalModelStateError,
    LocalModelStateMachine,
    recover_install_state,
)

# RC ID: RC-194. Verify lifecycle reachability and restart recovery from durable state.


def test_lifecycle_accepts_install_load_busy_and_unload_sequence() -> None:
    machine = LocalModelStateMachine(LocalModelState("gemma-3-1b-it", "ollama"))

    for event in (
        "download_started",
        "download_completed",
        "verified",
        "ready",
        "busy",
        "unload_started",
        "unloaded",
    ):
        result = machine.apply(event)  # type: ignore[arg-type]

    assert result.state.status == "unloaded"
    assert result.state.recovery_actions == ("install",)


@pytest.mark.parametrize(
    ("status", "event"),
    [
        ("not_installed", "ready"),
        ("ready", "download_completed"),
        ("busy", "download_started"),
        ("stopping", "busy"),
        ("corrupt", "busy"),
    ],
)
def test_impossible_lifecycle_jump_is_rejected(status: str, event: str) -> None:
    machine = LocalModelStateMachine(
        LocalModelState("qwen2.5-coder-1.5b-instruct", "ollama", status=status)  # type: ignore[arg-type]
    )

    with pytest.raises(LocalModelStateError, match="cannot apply"):
        machine.apply(event)  # type: ignore[arg-type]


def test_checksum_failure_exposes_repair_actions_and_missing_file_is_not_ready(tmp_path) -> None:
    installed = tmp_path / "gemma-3-1b-it"
    state_path = tmp_path / "install-state.json"
    state_path.write_text(
        json.dumps(
            {
                "model_id": "gemma-3-1b-it",
                "runner": "ollama",
                "phase": "ready",
                "status": "failed",
                "progress": 100,
                "checksum": "0" * 64,
                "installed_path": str(installed),
                "error": "checksum mismatch",
            }
        ),
        encoding="utf-8",
    )

    corrupt = recover_install_state(state_path)
    assert corrupt.status == "corrupt"
    assert corrupt.recovery_actions == ("retry", "repair", "uninstall")

    state_path.write_text(
        state_path.read_text(encoding="utf-8").replace('"status": "failed"', '"status": "ready"'),
        encoding="utf-8",
    )
    assert recover_install_state(state_path).status == "not_installed"

    installed.write_bytes(b"model")
    assert recover_install_state(state_path, runner_status="busy").status == "busy"
    assert recover_install_state(state_path, runner_status="ready").status == "ready"


def test_api_persists_backend_events_and_recovers_after_new_app(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("RABBIT_CODE_HOME", str(tmp_path / "data"))
    first = TestClient(create_app())

    assert first.get("/api/v1/local-models/gemma-3-1b-it/state").json()["state"]["status"] == (
        "not_installed"
    )
    for event, expected in (
        ("download_started", "downloading"),
        ("download_completed", "verifying"),
        ("verified", "loading"),
        ("ready", "ready"),
        ("busy", "busy"),
    ):
        response = first.post(
            "/api/v1/local-models/gemma-3-1b-it/events",
            json={"event": event},
        )
        assert response.status_code == 200
        assert response.json()["state"]["status"] == expected

    second = TestClient(create_app())
    recovered = second.get("/api/v1/local-models/gemma-3-1b-it/state")
    assert recovered.json()["state"]["status"] == "busy"

    impossible = second.post(
        "/api/v1/local-models/gemma-3-1b-it/events",
        json={"event": "download_completed"},
    )
    assert impossible.status_code == 409
