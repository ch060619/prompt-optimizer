from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from prompt_optimizer.local_health import run_health_check
from prompt_optimizer.local_install import LocalInstallCore, LocalInstallError
from prompt_optimizer.providers.runners import InMemoryRunnerAdapter

# RC ID: RC-193. Verify the post-install health contract and sanitized persisted report.


def test_health_check_runs_all_required_probes_and_persists_no_prompt(tmp_path: Path) -> None:
    runner = InMemoryRunnerAdapter("ollama")
    model_id = "google/gemma-3-1b-it"
    runner.pull(model_id)
    report_path = tmp_path / "health-report.json"
    source = tmp_path / "source.bin"
    source.write_bytes(b"health-gated-model")
    core = LocalInstallCore(tmp_path / "install")
    core.start(
        model_id="gemma-3-1b-it",
        runner="ollama",
        source=source,
        checksum=hashlib.sha256(source.read_bytes()).hexdigest(),
        license_accepted=True,
        health_check_required=True,
    )
    core.download_step(max_bytes=64)
    core.verify()
    core.install()
    report = run_health_check(
        runner,
        model_id=model_id,
        context_length=8,
        report_path=report_path,
        resource_probe=lambda: 220,
        state_recorder=core,
    )

    assert report.ready is True
    assert core.state is not None
    assert core.state.status == "ready"
    assert core.state.health_status == "passed"
    assert {check.name for check in report.checks} == {
        "runner_version",
        "model_load",
        "minimal_generation",
        "streaming_increment",
        "cancellation",
        "context_length",
        "stop_and_reload",
        "resource_peak",
    }
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["ready"] is True
    assert payload["resource_peak_bytes"] == 220
    assert "Rabbit Code health probe" not in report_path.read_text(encoding="utf-8")


def test_failed_health_check_rolls_back_health_required_install(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"health-gated-model")
    core = LocalInstallCore(tmp_path / "install")
    core.start(
        model_id="qwen2.5-coder-1.5b-instruct",
        runner="ollama",
        source=source,
        checksum=hashlib.sha256(source.read_bytes()).hexdigest(),
        license_accepted=True,
        health_check_required=True,
    )
    assert core.download_step(max_bytes=64)["event"] == "downloaded"
    assert core.verify()["event"] == "verified"
    assert core.install()["event"] == "installed"
    assert core.state is not None and core.state.status == "health_check"

    runner = InMemoryRunnerAdapter("ollama")
    runner.pull("qwen2.5-coder-1.5b-instruct")
    report = run_health_check(
        runner,
        model_id="qwen2.5-coder-1.5b-instruct",
        context_length=4,
        report_path=tmp_path / "health-report.json",
        resource_probe=lambda: None,
        state_recorder=core,
    )

    assert report.ready is False
    assert core.state is not None and core.state.status == "failed"
    assert core.state.health_status == "failed"
    with pytest.raises(LocalInstallError, match="not ready"):
        core.run()
