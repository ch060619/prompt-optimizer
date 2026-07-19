from __future__ import annotations

import hashlib
import threading

import pytest

from prompt_optimizer.local_install import LocalInstallCore, LocalInstallError

# RC ID: RC-191. Verify retry, pinned source metadata, endpoint policy, progress, and recovery.


def test_download_retries_transient_failure_and_preserves_pinned_metadata(tmp_path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"retryable-download")
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    calls = 0
    sleeps: list[float] = []

    def flaky_reader(path, offset, size):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("temporary network interruption")
        return path.read_bytes()[offset : offset + size]

    core = LocalInstallCore(tmp_path / "install", source_reader=flaky_reader, sleeper=sleeps.append)
    started = core.start(
        model_id="qwen2.5-coder-1.5b-instruct",
        runner="ollama",
        source=source,
        checksum=checksum,
        license_accepted=True,
        version="2e1fd397ee46e1388853d2af2c993145b0f1098a",
        mirror="https://mirror.example/models",
        proxy="http://proxy.example:8080",
        max_retries=1,
        retry_backoff_seconds=0.25,
    )
    assert started["state"]["version"] == "2e1fd397ee46e1388853d2af2c993145b0f1098a"
    assert core.download_step(max_bytes=64)["event"] == "downloaded"
    assert core.state is not None
    assert core.state.attempts == 1
    assert sleeps == [0.25]
    assert core.verify()["event"] == "verified"
    assert core.install()["event"] == "installed"


def test_failed_download_can_resume_and_endpoint_credentials_are_rejected(tmp_path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"recoverable")
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    allow = False

    def recoverable_reader(path, offset, size):
        if not allow:
            raise OSError("offline")
        return path.read_bytes()[offset : offset + size]

    core = LocalInstallCore(tmp_path / "install", source_reader=recoverable_reader)
    core.start(
        model_id="gemma-3-1b-it",
        runner="ollama",
        source=source,
        checksum=checksum,
        license_accepted=True,
        max_retries=1,
    )
    assert core.download_step(max_bytes=64)["event"] == "failed"
    assert core.state is not None and core.state.status == "failed"
    allow = True
    assert core.resume()["event"] == "resumed"
    assert core.download_step(max_bytes=64)["event"] == "downloaded"

    with pytest.raises(LocalInstallError, match="opaque reference"):
        LocalInstallCore(tmp_path / "other").start(
            model_id="gemma-3-1b-it",
            runner="ollama",
            source=source,
            checksum=checksum,
            license_accepted=True,
            proxy="http://user:password@proxy.example:8080",
        )


def test_checksum_failure_never_marks_model_ready(tmp_path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"checksum-protected")
    core = LocalInstallCore(tmp_path / "install")
    core.start(
        model_id="gemma-3-1b-it",
        runner="ollama",
        source=source,
        checksum="0" * 64,
        license_accepted=True,
    )

    assert core.download_step(max_bytes=64)["event"] == "downloaded"
    assert core.verify()["event"] == "failed"
    assert core.state is not None and core.state.status == "failed"
    assert not (tmp_path / "install" / "gemma-3-1b-it").exists()


def test_same_install_root_rejects_concurrent_download_writes(tmp_path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"concurrent-download")
    root = tmp_path / "install"
    started = threading.Event()
    release = threading.Event()
    result: list[dict[str, object]] = []

    def blocking_reader(path, offset, size):
        started.set()
        assert release.wait(timeout=2)
        return path.read_bytes()[offset : offset + size]

    first = LocalInstallCore(root, source_reader=blocking_reader)
    first.start(
        model_id="qwen2.5-coder-1.5b-instruct",
        runner="ollama",
        source=source,
        checksum=hashlib.sha256(source.read_bytes()).hexdigest(),
        license_accepted=True,
    )
    second = LocalInstallCore(root)
    worker = threading.Thread(
        target=lambda: result.append(first.download_step(max_bytes=64)),
        daemon=True,
    )
    worker.start()
    assert started.wait(timeout=2)
    with pytest.raises(LocalInstallError, match="already in progress"):
        second.download_step(max_bytes=64)
    release.set()
    worker.join(timeout=2)
    assert not worker.is_alive()
    assert result[0]["event"] == "downloaded"
