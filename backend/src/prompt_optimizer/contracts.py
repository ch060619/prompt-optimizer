from __future__ import annotations

from collections.abc import Iterator
from threading import Event
from typing import Any, Protocol, runtime_checkable

from prompt_optimizer.core.models import (
    DiffResult,
    ProjectSpace,
    PromptAnalysis,
    PromptTemplate,
    PromptVersion,
    ProviderHealth,
    ProviderSelectionScope,
    TaskKind,
    TaskRecord,
    TaskStatus,
    UserPublic,
    VersionSummary,
)

# RC ID: RC-066. Define replaceable Agent, Provider, Tool, Permission, Storage, and optimizer ports.


@runtime_checkable
class Agent(Protocol):
    def stream(
        self,
        request: Any,
        cancellation: Event | None = None,
    ) -> Iterator[Any]:
        pass


@runtime_checkable
class Provider(Protocol):
    name: str
    capabilities: Any

    def optimize(self, request: Any) -> Any:
        pass

    def stream(self, request: Any) -> Iterator[Any]:
        pass


@runtime_checkable
class ProviderCatalog(Protocol):
    def get(self, name: str) -> Provider:
        pass


@runtime_checkable
class Tool(Protocol):
    name: str

    def execute(self, arguments: dict[str, Any]) -> Any:
        pass


@runtime_checkable
class Permission(Protocol):
    def check(self, action: str, context: dict[str, Any]) -> bool:
        pass


@runtime_checkable
class PromptOptimizer(Protocol):
    def optimize(
        self,
        prompt: str,
        template: PromptTemplate | None = None,
        language_profile: Any = None,
        targets: Any = None,
    ) -> PromptAnalysis:
        pass


@runtime_checkable
class Storage(Protocol):
    def save_version(
        self,
        original_prompt: str,
        optimized_prompt: str,
        analysis: PromptAnalysis,
        owner_id: int = 1,
        project_id: int | None = None,
        accepted: bool = False,
        provider_used: str | None = None,
        model: str | None = None,
        selection_scope: ProviderSelectionScope = "default",
        provider_health: ProviderHealth = "healthy",
    ) -> int:
        pass

    def list_versions(self, owner_id: int = 1) -> list[VersionSummary]:
        pass

    def get_version(self, version_id: int, owner_id: int = 1) -> PromptVersion:
        pass

    def mark_version_accepted(self, version_id: int, owner_id: int) -> None:
        pass

    def delete_version(self, version_id: int, owner_id: int) -> None:
        pass

    def create_user(self, username: str, password_hash: str) -> UserPublic:
        pass

    def get_user_by_username(self, username: str) -> tuple[UserPublic, str] | None:
        pass

    def get_user(self, user_id: int) -> UserPublic:
        pass

    def list_project_spaces(self, owner_id: int) -> list[ProjectSpace]:
        pass

    def create_task(
        self,
        *,
        task_id: str,
        owner_id: int,
        kind: TaskKind,
        input_json: dict[str, Any],
    ) -> TaskRecord:
        pass

    def update_task(
        self,
        task_id: str,
        owner_id: int,
        *,
        status: TaskStatus,
        result_json: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        pass

    def get_task(self, task_id: str, owner_id: int) -> TaskRecord:
        pass


class DiffCalculator(Protocol):
    def compare(self, old: PromptVersion, new: PromptVersion) -> DiffResult:
        pass
