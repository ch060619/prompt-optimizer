from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.core.structure import StructuredInputError, StructuredPrompt
from prompt_optimizer.providers import (
    ModelRequest,
    ModelResponse,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
    ProviderRegistry,
)
from prompt_optimizer.providers.offline import OfflineRuleProvider
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

STRUCTURED_PROMPT = (
    "请处理 {{project_name}}。\n"
    "文件提及：@src/app.py\n"
    "附件：[[attachment:design.pdf]]\n"
    "命令：\n$ pytest tests/test_app.py\n"
    "输出格式：JSON\n"
    "```python\nprint('{{project_name}}')\n```"
)


class EchoProvider:
    name = "openai"
    capabilities = ProviderCapabilities()

    def __init__(self, *, mutate: bool = False) -> None:
        self.mutate = mutate
        self.seen_prompt = ""

    def optimize(self, request: ModelRequest) -> ModelResponse:
        self.seen_prompt = request.prompt
        output = request.prompt
        if self.mutate:
            output = output.replace("[[RABBIT_CODE_PROTECTED_0]]", "", 1)
        analysis = Analyzer().analyze(output)
        analysis.optimized_prompt = output
        return ModelResponse(analysis=analysis, provider_used=self.name, latency_ms=1)

    def stream(self, request: ModelRequest):
        response = self.optimize(request)
        yield ProviderEvent(ProviderEventType.STARTED)
        yield ProviderEvent(
            ProviderEventType.DELTA,
            text=response.analysis.optimized_prompt,
        )
        yield ProviderEvent(ProviderEventType.COMPLETED)


def _services(tmp_path: Path, provider: EchoProvider) -> AppServices:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "rc142.sqlite3"))
    services.providers = ProviderRegistry(
        services.optimizer,
        providers={"offline": services.providers.get("offline"), "openai": provider},
    )
    return services


def test_structure_parser_protects_required_input_spans() -> None:
    structure = StructuredPrompt.parse(STRUCTURED_PROMPT)
    protected = structure.protect()

    assert {segment.kind for segment in structure.segments} == {
        "placeholder",
        "file_mention",
        "attachment",
        "command",
        "output_format",
        "code_block",
    }
    assert "[[RABBIT_CODE_PROTECTED_" in protected
    assert structure.validate(protected) == STRUCTURED_PROMPT
    assert structure.validate(STRUCTURED_PROMPT) == STRUCTURED_PROMPT


def test_structure_parser_rejects_unclosed_code_fence() -> None:
    with pytest.raises(StructuredInputError, match="代码围栏未闭合"):
        StructuredPrompt.parse("请保留：\n```python\nprint('x')")


def test_internal_protected_structure_is_explicit_but_user_marker_stays_rejected() -> None:
    source = "输出格式：JSON"
    structure = StructuredPrompt.parse(source)
    protected = structure.protect()

    response = OfflineRuleProvider().optimize(
        ModelRequest(prompt=protected, protected_structure=structure)
    )

    assert response.analysis.optimized_prompt
    with pytest.raises(StructuredInputError, match="保留结构标记"):
        StructuredPrompt.parse(protected)


def test_service_restores_markers_before_returning_result(tmp_path: Path) -> None:
    provider = EchoProvider()
    services = _services(tmp_path, provider)

    result = services.optimize_and_save(
        original_prompt=STRUCTURED_PROMPT,
        prompt=STRUCTURED_PROMPT,
        template=None,
        provider_name="openai",
        owner_id=None,
    )

    assert "[[RABBIT_CODE_PROTECTED_" in provider.seen_prompt
    assert result.analysis.optimized_prompt == STRUCTURED_PROMPT
    assert "[[RABBIT_CODE_PROTECTED_" not in result.analysis.optimized_prompt


def test_api_rejects_structurally_changed_output_without_saving(tmp_path: Path) -> None:
    provider = EchoProvider(mutate=True)
    with TestClient(create_app(_services(tmp_path, provider))) as client:
        response = client.post(
            "/api/v1/optimize",
            json={"prompt": STRUCTURED_PROMPT, "provider": "openai"},
        )

    assert response.status_code == 400
    assert "结果未采用" in response.json()["detail"]


def test_streaming_output_is_validated_before_chunks_are_emitted(tmp_path: Path) -> None:
    provider = EchoProvider()
    with TestClient(create_app(_services(tmp_path, provider))) as client:
        with client.stream(
            "POST",
            "/api/v1/optimize/stream",
            json={"prompt": STRUCTURED_PROMPT, "provider": "openai"},
        ) as response:
            body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "event: completed" in body
    assert "RABBIT_CODE_PROTECTED" not in body
    assert "attachment:design.pdf" in body


def test_streaming_structural_failure_emits_recoverable_error(tmp_path: Path) -> None:
    provider = EchoProvider(mutate=True)
    with TestClient(create_app(_services(tmp_path, provider))) as client:
        with client.stream(
            "POST",
            "/api/v1/optimize/stream",
            json={"prompt": STRUCTURED_PROMPT, "provider": "openai"},
        ) as response:
            body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "event: error" in body
    assert "结果未采用" in body
    assert "event: completed" not in body
