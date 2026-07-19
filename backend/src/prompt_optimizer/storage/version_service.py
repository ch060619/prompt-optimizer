from __future__ import annotations

from prompt_optimizer.contracts import DiffCalculator, Storage
from prompt_optimizer.core.diff import DiffService
from prompt_optimizer.core.models import (
    DiffResult,
    PromptAnalysis,
    PromptVersion,
    ProviderHealth,
    ProviderSelectionScope,
    VersionSummary,
)
from prompt_optimizer.storage.service import StorageService


class VersionService:
    def __init__(
        self,
        storage: Storage | None = None,
        diff_service: DiffCalculator | None = None,
    ) -> None:
        self.storage = storage or StorageService()
        self.diff_service = diff_service or DiffService()

    def create(
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
        return self.storage.save_version(
            original_prompt,
            optimized_prompt,
            analysis,
            owner_id,
            project_id,
            accepted,
            provider_used,
            model,
            selection_scope,
            provider_health,
        )

    def list(self, owner_id: int = 1) -> list[VersionSummary]:
        return self.storage.list_versions(owner_id)

    def get(self, version_id: int, owner_id: int = 1) -> PromptVersion:
        return self.storage.get_version(version_id, owner_id)

    def mark_accepted(self, version_id: int, owner_id: int) -> PromptVersion:
        self.storage.mark_version_accepted(version_id, owner_id)
        return self.get(version_id, owner_id)

    def delete(self, version_id: int, owner_id: int) -> None:
        self.storage.delete_version(version_id, owner_id)

    def diff(self, old_id: int, new_id: int, owner_id: int = 1) -> DiffResult:
        return self.diff_service.compare(self.get(old_id, owner_id), self.get(new_id, owner_id))
