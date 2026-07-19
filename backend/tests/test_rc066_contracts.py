from __future__ import annotations

from pathlib import Path
from threading import Event
from typing import Any

import pytest
from scripts.check_dependency_boundaries import validate_dependency_boundaries

from prompt_optimizer.contracts import (
    Agent,
    Permission,
    PromptOptimizer,
    Provider,
    Storage,
    Tool,
)
from prompt_optimizer.core.models import PromptAnalysis
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage import version_service
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-066. Verify replaceable ports, constructor injection, and dependency boundaries.


class MemoryStorage:
    def save_version(self, *args: Any, **kwargs: Any) -> int:
        return 42

    def list_versions(self, owner_id: int = 1) -> list[Any]:
        return []

    def get_version(self, version_id: int, owner_id: int = 1) -> Any:
        raise KeyError(version_id)

    def mark_version_accepted(self, version_id: int, owner_id: int) -> None:
        return None

    def delete_version(self, version_id: int, owner_id: int) -> None:
        return None

    def create_user(self, username: str, password_hash: str) -> Any:
        raise NotImplementedError

    def get_user_by_username(self, username: str) -> None:
        return None

    def get_user(self, user_id: int) -> Any:
        raise KeyError(user_id)

    def list_project_spaces(self, owner_id: int) -> list[Any]:
        return []

    def create_task(self, **kwargs: Any) -> Any:
        raise NotImplementedError

    def update_task(self, task_id: str, owner_id: int, **kwargs: Any) -> None:
        return None

    def get_task(self, task_id: str, owner_id: int) -> Any:
        raise KeyError(task_id)


class FakeProvider:
    name = "fake"
    capabilities = object()

    def optimize(self, request: Any) -> Any:
        return request

    def stream(self, request: Any):
        yield request


class FakeAgent:
    def stream(self, request: Any, cancellation: Event | None = None):
        yield request


class FakeTool:
    name = "fake-tool"

    def execute(self, arguments: dict[str, Any]) -> Any:
        return arguments


class FakePermission:
    def check(self, action: str, context: dict[str, Any]) -> bool:
        return True


class FakeOptimizer:
    def optimize(self, prompt: str, template: Any = None) -> PromptAnalysis:
        raise NotImplementedError


def test_protocols_accept_replaceable_in_memory_implementations() -> None:
    assert isinstance(FakeAgent(), Agent)
    assert isinstance(FakeProvider(), Provider)
    assert isinstance(FakeTool(), Tool)
    assert isinstance(FakePermission(), Permission)
    assert isinstance(MemoryStorage(), Storage)
    assert isinstance(FakeOptimizer(), PromptOptimizer)


def test_services_accept_injected_ports() -> None:
    storage = MemoryStorage()
    versions = VersionService(storage=storage)
    optimizer = FakeOptimizer()
    services = AppServices(optimizer=optimizer, versions=versions)

    assert services.optimizer is optimizer
    assert services.versions is versions
    assert services.versions.storage is storage


def test_version_service_default_storage_constructor_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = object()
    monkeypatch.setattr(version_service, "StorageService", lambda: sentinel)

    assert VersionService().storage is sentinel


def test_surface_dependency_check_passes() -> None:
    repository_root = Path(__file__).resolve().parents[2]

    assert validate_dependency_boundaries(repository_root) == []
