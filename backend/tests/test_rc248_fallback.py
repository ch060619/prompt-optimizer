from __future__ import annotations

from pathlib import Path

import pytest

from prompt_optimizer.providers import ProviderRegistry
from prompt_optimizer.providers.local import LocalModelProvider, LocalRunnerHealth
from prompt_optimizer.providers.offline import OfflineRuleProvider
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-248. Verify local failure paths stay offline and preserve input.


class UnreadyRunner:
    def __init__(self, status: str) -> None:
        self.status = status

    def health(self) -> LocalRunnerHealth:
        return LocalRunnerHealth(False, status=self.status)  # type: ignore[arg-type]

    def generate(self, request):  # type: ignore[no-untyped-def]
        raise AssertionError("unready runner must not generate")

    def stream(self, request):  # type: ignore[no-untyped-def]
        raise AssertionError("unready runner must not stream")
        yield ""


@pytest.mark.parametrize(
    ("status", "reason", "action"),
    [
        ("not_installed", "not_installed", "install"),
        ("not_ready", "not_ready", "repair"),
        ("out_of_memory", "out_of_memory", "free_memory"),
    ],
)
def test_unready_local_model_falls_back_to_rules_without_external_request(
    tmp_path: Path,
    status: str,
    reason: str,
    action: str,
) -> None:
    providers = ProviderRegistry(
        providers={
            "offline": OfflineRuleProvider(),
            "local": LocalModelProvider(UnreadyRunner(status)),
        }
    )
    services = AppServices(
        providers=providers,
        versions=VersionService(StorageService(tmp_path / f"{status}.sqlite3")),
    )

    result = services.optimization.optimize(
        original_prompt="保留原始输入",
        prompt="保留原始输入",
        template=None,
        provider_name="local",
        owner_id=None,
    )

    assert "保留原始输入" in result.analysis.prompt
    assert result.analysis.optimized_prompt
    assert result.metadata.provider_used == "offline"
    assert result.metadata.fallback_used is True
    assert result.metadata.fallback_reason == reason
    assert result.metadata.recovery_action == action
