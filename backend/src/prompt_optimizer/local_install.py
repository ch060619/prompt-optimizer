from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from prompt_optimizer.local_model_state import LocalModelEventName, state_from_install_snapshot

# RC ID: RC-185. Keep local model installation resumable, cross-platform, and event-driven.
# RC ID: RC-191. Keep retries, pinned source metadata, and transfer failures in the same core.

InstallPhase = Literal["download", "verify", "install", "ready"]
InstallStatus = Literal[
    "idle",
    "downloading",
    "paused",
    "cancelled",
    "failed",
    "health_check",
    "ready",
    "running",
]
HealthStatus = Literal["pending", "passed", "failed"]
SourceReader = Callable[[Path, int, int], bytes]
Sleeper = Callable[[float], None]


class LocalInstallError(RuntimeError):
    """Raised when a local installation transition cannot be completed."""


@dataclass
class InstallSnapshot:
    model_id: str
    runner: str
    phase: InstallPhase
    status: InstallStatus
    progress: int
    checksum: str
    source_path: str | None = None
    installed_path: str | None = None
    error: str | None = None
    version: str = "local-source"
    mirror: str | None = None
    proxy: str | None = None
    max_retries: int = 0
    attempts: int = 0
    retry_backoff_seconds: float = 0.1
    license_confirmation_version: str | None = None
    license_url: str | None = None
    license_summary: str | None = None
    health_check_required: bool = False
    health_status: HealthStatus = "passed"
    health_report_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "runner": self.runner,
            "phase": self.phase,
            "status": self.status,
            "progress": self.progress,
            "checksum": self.checksum,
            "source_path": self.source_path,
            "installed_path": self.installed_path,
            "error": self.error,
            "version": self.version,
            "mirror": self.mirror,
            "proxy": self.proxy,
            "max_retries": self.max_retries,
            "attempts": self.attempts,
            "retry_backoff_seconds": self.retry_backoff_seconds,
            "license_confirmation_version": self.license_confirmation_version,
            "license_url": self.license_url,
            "license_summary": self.license_summary,
            "health_check_required": self.health_check_required,
            "health_status": self.health_status,
            "health_report_path": self.health_report_path,
        }


class LocalInstallCore:
    def __init__(
        self,
        root: Path,
        *,
        source_reader: SourceReader | None = None,
        sleeper: Sleeper | None = None,
    ) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = root / "install-state.json"
        self.part_path = root / "download.part"
        self._source_reader = source_reader or _read_source
        self._sleeper = sleeper or time.sleep
        self._download_lock = _download_lock(root)
        self._state: InstallSnapshot | None = self._load()

    @property
    def state(self) -> InstallSnapshot | None:
        return self._state

    def start(
        self,
        *,
        model_id: str,
        runner: str,
        source: Path,
        checksum: str,
        license_accepted: bool,
        version: str = "local-source",
        mirror: str | None = None,
        proxy: str | None = None,
        max_retries: int = 0,
        retry_backoff_seconds: float = 0.1,
        license_confirmation_version: str | None = None,
        license_url: str | None = None,
        license_summary: str | None = None,
        health_check_required: bool = False,
    ) -> dict[str, object]:
        if not license_accepted:
            raise LocalInstallError("model license must be accepted before download")
        if not source.is_file():
            raise LocalInstallError(f"model source does not exist: {source}")
        _validate_model_id(model_id)
        expected = _normalize_checksum(checksum)
        _validate_version(version)
        _validate_endpoint(mirror, name="mirror", schemes={"https"})
        _validate_endpoint(proxy, name="proxy", schemes={"http", "https"}, allow_credentials=False)
        _validate_endpoint(license_url, name="license_url", schemes={"https"})
        if license_confirmation_version is not None and not license_confirmation_version.strip():
            raise LocalInstallError("license_confirmation_version must not be empty")
        if license_summary is not None and not license_summary.strip():
            raise LocalInstallError("license_summary must not be empty")
        if max_retries < 0:
            raise LocalInstallError("max_retries must not be negative")
        if retry_backoff_seconds < 0:
            raise LocalInstallError("retry_backoff_seconds must not be negative")
        if self._state and self._state.model_id == model_id and self._state.checksum == expected:
            destination = Path(self._state.installed_path or "")
            if self._state.status in {"ready", "running"} and destination.is_file():
                return self._event("already_ready", "verified model already installed")
            if self._state.status in {"downloading", "paused"}:
                return self._event("already_started", "download already exists and can resume")
        elif self.part_path.exists():
            self.part_path.unlink()
        if (
            self._state
            and self._state.status in {"cancelled", "failed"}
            and self.part_path.exists()
        ):
            self.part_path.unlink()
        self._state = InstallSnapshot(
            model_id=model_id,
            runner=runner,
            phase="download",
            status="downloading",
            progress=0,
            checksum=expected,
            source_path=str(source),
            installed_path=str(self.root / model_id),
            version=version,
            mirror=mirror,
            proxy=proxy,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
            license_confirmation_version=license_confirmation_version,
            license_url=license_url,
            license_summary=license_summary,
            health_check_required=health_check_required,
            health_status="pending" if health_check_required else "passed",
        )
        self._save()
        return self._event("started", "download started")

    def download_step(self, *, max_bytes: int = 1024 * 1024) -> dict[str, object]:
        if not self._download_lock.acquire(blocking=False):
            raise LocalInstallError("download already in progress")
        try:
            return self._download_step(max_bytes=max_bytes)
        finally:
            self._download_lock.release()

    def _download_step(self, *, max_bytes: int) -> dict[str, object]:
        state = self._require_state()
        if state.phase != "download" or state.status not in {"downloading", "paused"}:
            raise LocalInstallError("download is not active")
        if max_bytes <= 0:
            raise LocalInstallError("max_bytes must be positive")
        source = Path(state.source_path or "")
        source_size = source.stat().st_size
        current_size = self.part_path.stat().st_size if self.part_path.exists() else 0
        if current_size > source_size:
            self.part_path.unlink()
            current_size = 0
        chunk: bytes | None = None
        for attempt in range(state.max_retries + 1):
            try:
                chunk = self._source_reader(source, current_size, max_bytes)
                break
            except (OSError, TimeoutError) as exc:
                state.attempts += 1
                if attempt == state.max_retries:
                    state.status = "failed"
                    state.error = f"download failed after {state.attempts} attempt(s): {exc}"
                    self._save()
                    return self._event("failed", "download failed; retry is available")
                self._sleeper(state.retry_backoff_seconds * (2**attempt))
        if chunk is None:
            raise LocalInstallError("download did not produce a chunk")
        with self.part_path.open("ab") as part_handle:
            part_handle.write(chunk)
            part_handle.flush()
            os.fsync(part_handle.fileno())
        state.status = "downloading"
        state.error = None
        state.progress = (
            100
            if source_size == 0
            else min(100, int(self.part_path.stat().st_size * 100 / source_size))
        )
        if self.part_path.stat().st_size >= source_size:
            state.phase = "verify"
            state.progress = 100
            self._save()
            return self._event("downloaded", "download complete; verification required")
        self._save()
        return self._event("progress", "download progress saved")

    def pause(self) -> dict[str, object]:
        state = self._require_state()
        if state.status != "downloading":
            raise LocalInstallError("download is not active")
        state.status = "paused"
        self._save()
        return self._event("paused", "download paused")

    def resume(self) -> dict[str, object]:
        state = self._require_state()
        if state.status not in {"paused", "cancelled", "failed"}:
            raise LocalInstallError("download is not resumable")
        state.status = "downloading"
        state.phase = "download"
        self._save()
        return self._event("resumed", "download resumed")

    def cancel(self) -> dict[str, object]:
        state = self._require_state()
        if self.part_path.exists():
            self.part_path.unlink()
        state.status = "cancelled"
        state.phase = "download"
        state.progress = 0
        self._save()
        return self._event("cancelled", "download cancelled")

    def verify(self) -> dict[str, object]:
        state = self._require_state()
        if state.phase != "verify" or not self.part_path.is_file():
            raise LocalInstallError("download is not ready for verification")
        actual = _sha256(self.part_path)
        if actual != state.checksum:
            state.status = "failed"
            state.error = "checksum mismatch"
            self._save()
            return self._event("failed", "checksum mismatch")
        state.status = "paused"
        state.phase = "install"
        state.error = None
        self._save()
        return self._event("verified", "checksum passed; installation ready")

    def install(self) -> dict[str, object]:
        state = self._require_state()
        if state.phase != "install" or not self.part_path.is_file():
            if state.status in {"ready", "running"}:
                return self._event("already_ready", "verified model already installed")
            raise LocalInstallError("model is not verified")
        destination = Path(state.installed_path or "")
        temporary = destination.with_name(f".{destination.name}.installing")
        if temporary.exists():
            temporary.unlink()
        os.replace(self.part_path, temporary)
        os.replace(temporary, destination)
        state.status = "health_check" if state.health_check_required else "ready"
        state.phase = "ready"
        state.progress = 100
        self._save()
        message = (
            "model installed; health check required"
            if state.health_check_required
            else "model installed"
        )
        return self._event("installed", message)

    def record_health_report(
        self,
        *,
        report_path: Path,
        passed: bool,
        error: str | None = None,
    ) -> dict[str, object]:
        state = self._require_state()
        if state.phase != "ready" or state.status not in {"health_check", "failed"}:
            raise LocalInstallError("installation is not waiting for a health check")
        state.health_report_path = str(report_path)
        state.health_status = "passed" if passed else "failed"
        state.error = None if passed else (error or "health check failed")
        state.status = "ready" if passed else "failed"
        self._save()
        return self._event(
            "health_ready" if passed else "health_failed",
            state.error or "health check passed",
        )

    def run(self) -> dict[str, object]:
        state = self._require_state()
        if state.status != "ready":
            raise LocalInstallError("model is not ready to run")
        state.status = "running"
        self._save()
        return self._event("running", "local runner ready")

    def _require_state(self) -> InstallSnapshot:
        if self._state is None:
            raise LocalInstallError("installation has not started")
        return self._state

    def _event(self, event: str, message: str) -> dict[str, object]:
        state = self._require_state()
        state_payload = state.to_dict()
        lifecycle_state = state_from_install_snapshot(state_payload)
        lifecycle_event = _lifecycle_event_for(event, state_payload)
        return {
            "event": event,
            "message": message,
            "lifecycle_event": lifecycle_event,
            "lifecycle_status": lifecycle_state.status,
            "recovery_actions": list(lifecycle_state.recovery_actions),
            "state": state_payload,
        }

    def _save(self) -> None:
        if self._state is None:
            return
        temporary = self.state_path.with_name(f".{self.state_path.name}.tmp")
        temporary.write_text(
            json.dumps(self._state.to_dict(), ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.state_path)

    def _load(self) -> InstallSnapshot | None:
        if not self.state_path.is_file():
            return None
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            return InstallSnapshot(**payload)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise LocalInstallError(f"invalid install state: {self.state_path}") from exc


def _normalize_checksum(value: str) -> str:
    normalized = value.removeprefix("sha256:").strip().lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise LocalInstallError("checksum must be a SHA-256 hex digest")
    return normalized


def _validate_model_id(value: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value):
        raise LocalInstallError("model_id must be a safe file name")


def _validate_version(value: str) -> None:
    if not value.strip() or any(character.isspace() for character in value):
        raise LocalInstallError("version must be a non-empty pinned value")


def _validate_endpoint(
    value: str | None,
    *,
    name: str,
    schemes: set[str],
    allow_credentials: bool = True,
) -> None:
    if value is None:
        return
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in schemes or not parsed.hostname:
        allowed = ", ".join(sorted(schemes))
        raise LocalInstallError(f"{name} must be a valid endpoint using {allowed}")
    if not allow_credentials and (parsed.username or parsed.password):
        raise LocalInstallError(f"{name} credentials must use an opaque reference")


def _read_source(path: Path, offset: int, max_bytes: int) -> bytes:
    with path.open("rb") as source_handle:
        source_handle.seek(offset)
        return source_handle.read(max_bytes)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


_DOWNLOAD_LOCK_GUARD = threading.Lock()
_DOWNLOAD_LOCKS: dict[Path, threading.Lock] = {}


def _download_lock(root: Path) -> threading.Lock:
    key = root.resolve()
    with _DOWNLOAD_LOCK_GUARD:
        lock = _DOWNLOAD_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _DOWNLOAD_LOCKS[key] = lock
        return lock


def _lifecycle_event_for(event: str, state: dict[str, object]) -> LocalModelEventName:
    if event == "failed":
        error = state.get("error")
        return "corrupt" if isinstance(error, str) and "checksum" in error.lower() else "failed"
    if event in {"started", "resumed"}:
        return "download_started"
    if event == "progress":
        return "download_progress"
    if event == "paused":
        return "download_paused"
    if event == "downloaded":
        return "download_completed"
    if event == "verified":
        return "verified"
    if event == "installed":
        return "load_started" if state.get("status") == "health_check" else "ready"
    if event == "health_ready":
        return "ready"
    if event == "running":
        return "busy"
    if event == "cancelled":
        return "reset"
    return "ready"
