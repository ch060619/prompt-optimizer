from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.core.models import OptimizationTargets
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.providers import (
    ModelRequest,
    ModelResponse,
    ProviderCapabilities,
    ProviderRegistry,
)
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService


# RC ID: RC-154. Verify target routing remains user context for every provider boundary.
class CapturingProvider:
    name = "openai"
    capabilities = ProviderCapabilities()

    def __init__(self) -> None:
        self.request: ModelRequest | None = None

    def optimize(self, request: ModelRequest) -> ModelResponse:
        self.request = request
        analysis = Analyzer().analyze(request.prompt)
        analysis.optimized_prompt = request.prompt
        return ModelResponse(analysis=analysis, provider_used=self.name, latency_ms=1)

    def stream(self, request: ModelRequest):
        yield from ()


def test_optimizer_applies_only_requested_targets() -> None:
    targets = OptimizationTargets(
        clarity=True,
        completeness=False,
        constraints=False,
        format=False,
        role=False,
        examples=False,
        code_task=False,
        conciseness=True,
        language_preservation=True,
    )

    optimized = Optimizer().optimize(
        "Write a concise API summary",
        targets=targets,
    ).optimized_prompt or ""

    assert "Clarity:" in optimized
    assert "Conciseness:" in optimized
    assert "Completeness:" not in optimized
    assert "Output format:" not in optimized


def test_service_keeps_targets_out_of_system_prompt_and_on_request(tmp_path: Path) -> None:
    provider = CapturingProvider()
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "rc154.sqlite3"))
    services.providers = ProviderRegistry(
        services.optimizer,
        providers={"offline": services.providers.get("offline"), "openai": provider},
    )
    targets = OptimizationTargets(code_task=True, examples=False)

    services.optimize_and_save(
        original_prompt="Write a Python function",
        prompt="Write a Python function",
        template=None,
        provider_name="openai",
        targets=targets,
        owner_id=None,
    )

    assert provider.request is not None
    assert provider.request.targets == targets
    assert "Code task" not in provider.request.system_prompt


def test_api_rejects_an_empty_target_selection() -> None:
    response = TestClient(create_app(AppServices())).post(
        "/api/v1/optimize",
        json={
            "prompt": "Write a release note",
            "targets": {
                "clarity": False,
                "completeness": False,
                "constraints": False,
                "format": False,
                "role": False,
                "examples": False,
                "code_task": False,
                "conciseness": False,
                "language_preservation": False,
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "至少选择一项优化目标。"
