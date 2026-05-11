from __future__ import annotations

from prompt_optimizer.core.diff import DiffService
from prompt_optimizer.core.models import DiffResult, PromptAnalysis, PromptVersion, VersionSummary
from prompt_optimizer.storage.service import StorageService


class VersionService:
    def __init__(
        self,
        storage: StorageService | None = None,
        diff_service: DiffService | None = None,
    ) -> None:
        self.storage = storage or StorageService()
        self.diff_service = diff_service or DiffService()

    def create(self, original_prompt: str, optimized_prompt: str, analysis: PromptAnalysis) -> int:
        return self.storage.save_version(original_prompt, optimized_prompt, analysis)

    def list(self) -> list[VersionSummary]:
        return self.storage.list_versions()

    def get(self, version_id: int) -> PromptVersion:
        return self.storage.get_version(version_id)

    def diff(self, old_id: int, new_id: int) -> DiffResult:
        return self.diff_service.compare(self.get(old_id), self.get(new_id))
