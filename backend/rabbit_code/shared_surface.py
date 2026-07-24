from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar, Protocol

from .permissions import PermissionMode, PermissionPolicy

# RC ID: RC-106. Share provider, model, session, permission, and optimization state across surfaces.


class SurfaceKind(StrEnum):
    CLI = "cli"
    GUI = "gui"
    API = "api"


class SharedSurfaceConflict(RuntimeError):
    """Raised when a surface writes against an older shared-state revision."""


@dataclass(frozen=True)
class PromptVersionReference:
    version_id: str
    accepted: bool = False


@dataclass(frozen=True)
class FileChangeReference:
    path: str
    before_sha256: str
    after_sha256: str
    checkpoint_id: str | None = None


@dataclass(frozen=True)
class SharedEvent:
    revision: int
    event_type: str


class PromptOptimizer(Protocol):
    def optimize(self, prompt: str, *, provider: str, model: str) -> str:
        pass


@dataclass(frozen=True)
class ProviderReference:
    name: str
    endpoint: str
    api_key_ref: str | None = None


@dataclass(frozen=True)
class ModelDescriptor:
    name: str
    provider: str
    capabilities: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SharedSnapshot:
    provider: ProviderReference | None
    model: str | None
    model_catalog: tuple[ModelDescriptor, ...]
    session_id: str | None
    permission_mode: PermissionMode
    revision: int = 0
    prompt_versions: tuple[PromptVersionReference, ...] = ()
    file_changes: tuple[FileChangeReference, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": (
                {
                    "name": self.provider.name,
                    "endpoint": self.provider.endpoint,
                    "api_key_ref": self.provider.api_key_ref,
                }
                if self.provider
                else None
            ),
            "model": self.model,
            "model_catalog": [
                {
                    "name": item.name,
                    "provider": item.provider,
                    "capabilities": sorted(item.capabilities),
                }
                for item in self.model_catalog
            ],
            "session_id": self.session_id,
            "permission_mode": self.permission_mode.value,
            "revision": self.revision,
            "prompt_versions": [
                {"version_id": item.version_id, "accepted": item.accepted}
                for item in self.prompt_versions
            ],
            "file_changes": [
                {
                    "path": item.path,
                    "before_sha256": item.before_sha256,
                    "after_sha256": item.after_sha256,
                    "checkpoint_id": item.checkpoint_id,
                }
                for item in self.file_changes
            ],
        }


class SharedSurfaceStore:
    """Persist the non-sensitive state shared by CLI and GUI processes."""

    _schema_version = 1
    _path_locks: ClassVar[dict[Path, threading.RLock]] = {}
    _path_locks_guard: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self, path: Path) -> None:
        self.path = path.expanduser().resolve()
        self.lock_path = self.path.with_name(f"{self.path.name}.lock")

    def read(self) -> dict[str, Any]:
        with self._locked():
            return self._read_unlocked()

    def update(
        self,
        mutate: Callable[[dict[str, Any]], None],
        *,
        expected_revision: int | None = None,
        event_type: str = "state.updated",
    ) -> dict[str, Any]:
        with self._locked():
            state = self._read_unlocked()
            current_revision = int(state.get("revision", 0))
            if expected_revision is not None and expected_revision != current_revision:
                raise SharedSurfaceConflict(
                    f"shared state changed from revision {expected_revision} to {current_revision}"
                )
            mutate(state)
            next_revision = current_revision + 1
            state["revision"] = next_revision
            events = state.get("events", [])
            if not isinstance(events, list):
                raise ValueError("shared surface events must be a list")
            events.append({"revision": next_revision, "type": event_type})
            state["events"] = events[-512:]
            self._write_unlocked(state)
            return state

    def events_since(self, revision: int) -> tuple[SharedEvent, ...]:
        if revision < 0:
            raise ValueError("revision must be non-negative")
        state = self.read()
        events = state.get("events", [])
        if not isinstance(events, list):
            raise ValueError("shared surface events must be a list")
        return tuple(
            SharedEvent(int(item["revision"]), str(item["type"]))
            for item in events
            if isinstance(item, dict) and int(item.get("revision", 0)) > revision
        )

    def _read_unlocked(self) -> dict[str, Any]:
        if not self.path.is_file():
            return self._default_state()
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"shared surface state is not valid JSON: {self.path}") from exc
        if not isinstance(state, dict) or state.get("schema_version") != self._schema_version:
            raise ValueError("unsupported shared surface state schema")
        return state

    def _write_unlocked(self, state: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    @staticmethod
    def _default_state() -> dict[str, Any]:
        return {
            "schema_version": 1,
            "revision": 0,
            "events": [],
            "provider": None,
            "model": None,
            "model_catalog": [],
            "session_id": None,
            "permission_mode": PermissionMode.PLAN.value,
            "prompt_versions": [],
            "file_changes": [],
        }

    @contextmanager
    def _locked(self) -> Iterator[None]:
        with self._thread_lock():
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            with self.lock_path.open("a+b") as lock:
                lock.seek(0, os.SEEK_END)
                if lock.tell() == 0:
                    lock.write(b"0")
                    lock.flush()
                lock.seek(0)
                unlock = self._acquire_file_lock(lock)
                try:
                    yield
                finally:
                    unlock()

    @contextmanager
    def _thread_lock(self) -> Iterator[None]:
        with self._path_locks_guard:
            lock = self._path_locks.setdefault(self.path, threading.RLock())
        with lock:
            yield

    @staticmethod
    def _acquire_file_lock(lock: Any) -> Callable[[], None]:
        if os.name == "nt":
            import msvcrt

            deadline = time.monotonic() + 30
            while True:
                try:
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as exc:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            "timed out waiting for shared surface state lock"
                        ) from exc
                    time.sleep(0.01)

            def release() -> None:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)

            return release

        import fcntl

        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)  # type: ignore[attr-defined]

        def unix_release() -> None:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]

        return unix_release


@dataclass
class SharedSurfaceContext:
    workspace_root: Path
    permission_policy: PermissionPolicy
    optimizer: PromptOptimizer
    store: SharedSurfaceStore | None = field(default=None, repr=False)
    provider: ProviderReference | None = None
    model: str | None = None
    session_id: str | None = None
    model_catalog: list[ModelDescriptor] = field(default_factory=list)
    prompt_versions: list[PromptVersionReference] = field(default_factory=list)
    file_changes: list[FileChangeReference] = field(default_factory=list)
    revision: int = 0

    @classmethod
    def create(
        cls,
        workspace_root: Path,
        optimizer: PromptOptimizer,
        *,
        permission_policy: PermissionPolicy | None = None,
        state_path: Path | None = None,
    ) -> SharedSurfaceContext:
        root = workspace_root.expanduser().resolve()
        if not root.is_dir():
            raise ValueError("workspace root must be a directory")
        store_path = state_path or root / ".rabbit-code" / "shared-surface.json"
        context = cls(
            root,
            permission_policy or PermissionPolicy(root),
            optimizer,
            SharedSurfaceStore(store_path),
        )
        context._refresh()
        return context

    def configure_provider(self, provider: ProviderReference) -> None:
        if not provider.name or not provider.endpoint:
            raise ValueError("provider name and endpoint are required")

        def mutate(state: dict[str, Any]) -> None:
            state["provider"] = {
                "name": provider.name,
                "endpoint": provider.endpoint,
                "api_key_ref": provider.api_key_ref,
            }
            if state.get("model") is not None and not self._model_exists(state, state["model"]):
                state["model"] = None

        self._update(mutate, event_type="provider.changed")

    def set_model_catalog(self, models: Sequence[ModelDescriptor]) -> None:
        normalized = tuple(models)
        if len({item.name for item in normalized}) != len(normalized):
            raise ValueError("model names must be unique")

        def mutate(state: dict[str, Any]) -> None:
            state["model_catalog"] = [
                {
                    "name": item.name,
                    "provider": item.provider,
                    "capabilities": sorted(item.capabilities),
                }
                for item in normalized
            ]
            if state.get("model") is not None and not self._model_exists(state, state["model"]):
                state["model"] = None

        self._update(mutate, event_type="model_catalog.changed")

    def select_model(self, model: str) -> None:
        def mutate(state: dict[str, Any]) -> None:
            if not self._model_exists(state, model):
                raise KeyError(f"model is not in the shared catalog: {model}")
            state["model"] = model

        self._update(mutate, event_type="model.changed")

    def set_session(self, session_id: str) -> None:
        if not session_id.strip():
            raise ValueError("session_id is required")
        self._update(
            lambda state: state.update(session_id=session_id),
            event_type="session.changed",
        )

    def set_permission_mode(self, mode: PermissionMode) -> None:
        self._refresh()
        if mode is self.permission_policy.mode:
            return
        self.permission_policy.switch_mode(mode, explicit_confirmation=True)
        self._update(
            lambda state: state.update(permission_mode=mode.value),
            event_type="permission.changed",
        )

    def record_prompt_version(self, version_id: str, *, accepted: bool = False) -> None:
        if not version_id.strip():
            raise ValueError("version_id is required")

        def mutate(state: dict[str, Any]) -> None:
            versions = state.setdefault("prompt_versions", [])
            if not isinstance(versions, list):
                raise ValueError("shared prompt versions must be a list")
            versions[:] = [
                item for item in versions
                if not isinstance(item, dict) or item.get("version_id") != version_id
            ]
            versions.append({"version_id": version_id, "accepted": accepted})

        self._update(mutate, event_type="prompt_version.changed")

    def record_file_change(
        self,
        path: str,
        *,
        before_sha256: str,
        after_sha256: str,
        checkpoint_id: str | None = None,
    ) -> None:
        if not path.strip() or not before_sha256.strip() or not after_sha256.strip():
            raise ValueError("file change path and hashes are required")

        def mutate(state: dict[str, Any]) -> None:
            changes = state.setdefault("file_changes", [])
            if not isinstance(changes, list):
                raise ValueError("shared file changes must be a list")
            changes.append(
                {
                    "path": path,
                    "before_sha256": before_sha256,
                    "after_sha256": after_sha256,
                    "checkpoint_id": checkpoint_id,
                }
            )

        self._update(mutate, event_type="file_change.changed")

    def events_since(self, revision: int) -> tuple[SharedEvent, ...]:
        return self._ensure_store().events_since(revision)

    def update_optimistic(
        self,
        expected_revision: int,
        mutate: Callable[[dict[str, Any]], None],
        *,
        event_type: str = "state.updated",
    ) -> None:
        state = self._ensure_store().update(
            mutate,
            expected_revision=expected_revision,
            event_type=event_type,
        )
        self._apply_state(state)

    def optimize(self, prompt: str) -> str:
        self._refresh()
        if self.provider is None or self.model is None:
            raise ValueError("shared provider and model must be selected")
        return self.optimizer.optimize(prompt, provider=self.provider.name, model=self.model)

    def snapshot(self) -> SharedSnapshot:
        self._refresh()
        return SharedSnapshot(
            provider=self.provider,
            model=self.model,
            model_catalog=tuple(self.model_catalog),
            session_id=self.session_id,
            permission_mode=self.permission_policy.mode,
            revision=self.revision,
            prompt_versions=tuple(self.prompt_versions),
            file_changes=tuple(self.file_changes),
        )

    def _refresh(self) -> None:
        state = self._ensure_store().read()
        self._apply_state(state)

    def _ensure_store(self) -> SharedSurfaceStore:
        if self.store is None:
            self.store = SharedSurfaceStore(
                self.workspace_root / ".rabbit-code" / "shared-surface.json"
            )
        return self.store

    def _update(
        self,
        mutate: Callable[[dict[str, Any]], None],
        *,
        event_type: str = "state.updated",
    ) -> None:
        state = self._ensure_store().update(mutate, event_type=event_type)
        self._apply_state(state)

    def _apply_state(self, state: dict[str, Any]) -> None:
        provider = state.get("provider")
        if provider is not None and not isinstance(provider, dict):
            raise ValueError("shared provider state must be an object or null")
        self.provider = (
            ProviderReference(
                name=str(provider["name"]),
                endpoint=str(provider["endpoint"]),
                api_key_ref=(
                    str(provider["api_key_ref"])
                    if provider.get("api_key_ref") is not None
                    else None
                ),
            )
            if provider is not None
            else None
        )
        raw_catalog = state.get("model_catalog")
        if not isinstance(raw_catalog, list):
            raise ValueError("shared model catalog must be a list")
        self.model_catalog = [
            ModelDescriptor(
                name=str(item["name"]),
                provider=str(item["provider"]),
                capabilities=frozenset(str(capability) for capability in item["capabilities"]),
            )
            for item in raw_catalog
        ]
        if len({item.name for item in self.model_catalog}) != len(self.model_catalog):
            raise ValueError("model names must be unique")
        self.model = str(state["model"]) if state.get("model") is not None else None
        if self.model is not None and not any(
            item.name == self.model for item in self.model_catalog
        ):
            raise ValueError("shared model is not in the model catalog")
        self.session_id = (
            str(state["session_id"]) if state.get("session_id") is not None else None
        )
        self.permission_policy.restore_mode(PermissionMode(state["permission_mode"]))
        self.revision = int(state.get("revision", 0))
        raw_versions = state.get("prompt_versions", [])
        if not isinstance(raw_versions, list):
            raise ValueError("shared prompt versions must be a list")
        self.prompt_versions = [
            PromptVersionReference(
                version_id=str(item["version_id"]),
                accepted=bool(item.get("accepted", False)),
            )
            for item in raw_versions
            if isinstance(item, dict) and isinstance(item.get("version_id"), str)
        ]
        raw_changes = state.get("file_changes", [])
        if not isinstance(raw_changes, list):
            raise ValueError("shared file changes must be a list")
        self.file_changes = [
            FileChangeReference(
                path=str(item["path"]),
                before_sha256=str(item["before_sha256"]),
                after_sha256=str(item["after_sha256"]),
                checkpoint_id=(
                    str(item["checkpoint_id"])
                    if item.get("checkpoint_id") is not None
                    else None
                ),
            )
            for item in raw_changes
            if isinstance(item, dict)
            and all(
                isinstance(item.get(name), str)
                for name in ("path", "before_sha256", "after_sha256")
            )
        ]

    @staticmethod
    def _model_exists(state: dict[str, Any], model: object) -> bool:
        return any(item.get("name") == model for item in state["model_catalog"])


@dataclass(frozen=True)
class SurfaceClient:
    surface: SurfaceKind
    context: SharedSurfaceContext

    def snapshot(self) -> SharedSnapshot:
        return self.context.snapshot()

    def optimize(self, prompt: str) -> str:
        return self.context.optimize(prompt)
