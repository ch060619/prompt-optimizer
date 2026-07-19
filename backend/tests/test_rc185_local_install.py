from __future__ import annotations

import hashlib
import json
import subprocess

import pytest

from prompt_optimizer.local_install import LocalInstallCore, LocalInstallError

# RC ID: RC-185. Verify resumable core state and the JSON CLI wrapper agree.


def test_install_core_resumes_after_restart_and_is_idempotent(tmp_path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"rabbit-code-local-model" * 200)
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    root = tmp_path / "install"
    core = LocalInstallCore(root)

    core.start(
        model_id="gemma-3-4b",
        runner="ollama",
        source=source,
        checksum=checksum,
        license_accepted=True,
    )
    core.download_step(max_bytes=32)
    core.pause()

    resumed = LocalInstallCore(root)
    resumed.resume()
    while resumed.state is not None and resumed.state.phase == "download":
        resumed.download_step(max_bytes=32)
    assert resumed.verify()["event"] == "verified"
    assert resumed.install()["event"] == "installed"
    assert resumed.run()["event"] == "running"
    assert LocalInstallCore(root).install()["event"] == "already_ready"
    assert json.loads((root / "install-state.json").read_text(encoding="utf-8"))["status"] == (
        "running"
    )


def test_start_is_resumable_and_verified_state_cannot_append_download_bytes(tmp_path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"resumable-model")
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    root = tmp_path / "install"
    core = LocalInstallCore(root)

    core.start(
        model_id="gemma-3-4b",
        runner="ollama",
        source=source,
        checksum=checksum,
        license_accepted=True,
    )
    core.download_step(max_bytes=4)
    resumed_event = core.start(
        model_id="gemma-3-4b",
        runner="ollama",
        source=source,
        checksum=checksum,
        license_accepted=True,
    )
    assert resumed_event["event"] == "already_started"
    while core.state is not None and core.state.phase == "download":
        core.download_step(max_bytes=4)
    core.verify()
    with pytest.raises(LocalInstallError, match="download is not active"):
        core.download_step(max_bytes=4)
    assert core.install()["event"] == "installed"


def test_model_id_cannot_escape_install_root(tmp_path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"model")
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()

    with pytest.raises(LocalInstallError, match="safe file name"):
        LocalInstallCore(tmp_path / "install").start(
            model_id="../outside",
            runner="ollama",
            source=source,
            checksum=checksum,
            license_accepted=True,
        )


def test_cli_wrapper_uses_the_same_persisted_state(tmp_path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"cli-shared-state")
    root = tmp_path / "install"
    python = ".venv/Scripts/python.exe"
    base = [
        python,
        "scripts/local_model_install.py",
        "--root",
        str(root),
        "--source",
        str(source),
        "--model-id",
        "qwen2.5-coder-7b",
        "--version",
        "test-revision",
        "--mirror",
        "https://mirror.example/models",
        "--proxy",
        "http://proxy.example:8080",
        "--license-confirmation-version",
        "Apache-2.0",
        "--license-url",
        "https://www.apache.org/licenses/LICENSE-2.0",
        "--license-summary",
        "Apache-2.0 terms apply to user downloads",
        "--retries",
        "1",
        "--accept-license",
    ]

    start = subprocess.run([*base, "start"], check=True, capture_output=True, text=True)
    assert json.loads(start.stdout)["event"] == "started"
    while True:
        result = subprocess.run(
            [
                python,
                "scripts/local_model_install.py",
                "download",
                "--root",
                str(root),
                "--step-bytes",
                "4",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        if json.loads(result.stdout)["state"]["phase"] == "verify":
            break
    verify = subprocess.run(
        [python, "scripts/local_model_install.py", "verify", "--root", str(root)],
        check=True,
        capture_output=True,
        text=True,
    )
    install = subprocess.run(
        [python, "scripts/local_model_install.py", "install", "--root", str(root)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(verify.stdout)["event"] == "verified"
    assert json.loads(install.stdout)["event"] == "installed"
    assert json.loads(start.stdout)["state"]["license_confirmation_version"] == "Apache-2.0"
