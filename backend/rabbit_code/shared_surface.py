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

    def update(self, mutate: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
        with self._locked():
            state = self._read_unlocked()
            mutate(state)
            self._write_unlocked(state)
            return state

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
            "provider": None,
            "model": None,
            "model_catalog": [],
            "session_id": None,
            "permission_mode": PermissionMode.PLAN.value,
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

        self._update(mutate)

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

        self._update(mutate)

    def select_model(self, model: str) -> None:
        def mutate(state: dict[str, Any]) -> None:
            if not self._model_exists(state, model):
                raise KeyError(f"model is not in the shared catalog: {model}")
            state["model"] = model

        self._update(mutate)

    def set_session(self, session_id: str) -> None:
        if not session_id.strip():
            raise ValueError("session_id is required")
        self._update(lambda state: state.update(session_id=session_id))

    def set_permission_mode(self, mode: PermissionMode) -> None:
        self._refresh()
        if mode is self.permission_policy.mode:
            return
        self.permission_policy.switch_mode(mode, explicit_confirmation=True)
        self._update(lambda state: state.update(permission_mode=mode.value))

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

    def _update(self, mutate: Callable[[dict[str, Any]], None]) -> None:
        state = self._ensure_store().update(mutate)
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
