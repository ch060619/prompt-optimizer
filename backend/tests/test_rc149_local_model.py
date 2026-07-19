from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from prompt_optimizer.core.models import OptimizeMetadata, PromptAnalysis
from prompt_optimizer.providers import (
    ModelRequest,
    ProviderRegistry,
)
from prompt_optimizer.providers.local import (
    LocalModelProvider,
    LocalModelRunner,
    LocalRunnerHealth,
    UnavailableLocalRunner,
)
from prompt_optimizer.providers.offline import OfflineRuleProvider
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-149. Verify local runner Adapter generation and streaming without remote HTTP.


class FakeLocalRunner:
    def __init__(self) -> None:
        self.requests: list[ModelRequest] = []

    def health(self) -> LocalRunnerHealth:
        return LocalRunnerHealth(True, "gemma-3-4b", "ready")

    def generate(self, request: ModelRequest) -> str:
        self.requests.append(request)
        return "本地模型优化结果。目标：完成任务。输出格式：列表。限制：保持本地处理。"

    def stream(self, request: ModelRequest) -> Iterator[str]:
        self.requests.append(request)
        yield "本地模型"
        yield "流式结果。"


class FailingLocalRunner:
    def __init__(self, error: BaseException) -> None:
        self.error = error

    def health(self) -> LocalRunnerHealth:
        return LocalRunnerHealth(True, "gemma-3-4b", "ready")

    def generate(self, request: ModelRequest) -> str:
        raise self.error

    def stream(self, request: ModelRequest) -> Iterator[str]:
        raise self.error
        yield ""


class UnreadyLocalRunner:
    def __init__(self, status: str) -> None:
        self.status = status

    def health(self) -> LocalRunnerHealth:
        return LocalRunnerHealth(False, status=self.status)  # type: ignore[arg-type]

    def generate(self, request: ModelRequest) -> str:
        raise AssertionError("unready runners must not generate")

    def stream(self, request: ModelRequest) -> Iterator[str]:
        raise AssertionError("unready runners must not stream")
        yield ""


def build_services(tmp_path: Path, runner: LocalModelRunner) -> AppServices:
    storage = StorageService(tmp_path / "rc149.sqlite3")
    registry = ProviderRegistry(
        providers={
            "offline": OfflineRuleProvider(),
            "local": LocalModelProvider(runner),
        }
    )
    return AppServices(providers=registry, versions=VersionService(storage))


def test_local_provider_uses_ready_runner_and_reports_local_metadata(tmp_path: Path) -> None:
    runner = FakeLocalRunner()
    services = build_services(tmp_path, runner)

    result = services.optimization.optimize(
        original_prompt="写一个本地任务",
        prompt="写一个本地任务",
        template=None,
        provider_name="local",
        model="gemma-3-4b",
        owner_id=None,
    )

    assert result.metadata.provider_used == "local"
    assert result.metadata.execution_location == "local"
    assert result.metadata.model == "gemma-3-4b"
    assert result.metadata.fallback_used is False
    assert len(runner.requests) == 1


def test_local_provider_streams_runner_chunks_without_cloud_provider(tmp_path: Path) -> None:
    runner = FakeLocalRunner()
    services = build_services(tmp_path, runner)
    events = list(
        services.optimization.stream(
            original_prompt="流式本地任务",
            prompt="流式本地任务",
            template=None,
            provider_name="local",
            model="gemma-3-4b",
            owner_id=None,
            request_id="rc149-local-stream",
        )
    )

    assert events[0].event == "analysis"
    assert events[-1].event == "completed"
    assert [event.data for event in events if event.event == "chunk"] == ["本地模型", "流式结果。"]
    assert len(runner.requests) == 1
    assert all(
        not isinstance(event.data, PromptAnalysis) or event.data.prompt == "流式本地任务"
        for event in events
    )


@pytest.mark.parametrize(
    ("status", "reason", "action", "code"),
    [
        ("not_installed", "not_installed", "install", "LOCAL_MODEL_NOT_INSTALLED"),
        ("not_ready", "not_ready", "repair", "LOCAL_MODEL_NOT_READY"),
        ("out_of_memory", "out_of_memory", "free_memory", "LOCAL_MODEL_OUT_OF_MEMORY"),
        ("timeout", "timeout", "retry", "LOCAL_MODEL_TIMEOUT"),
    ],
)
def test_local_health_failures_fall_back_with_recovery_metadata(
    tmp_path: Path,
    status: str,
    reason: str,
    action: str,
    code: str,
) -> None:
    services = build_services(tmp_path, UnreadyLocalRunner(status))

    result = services.optimization.optimize(
        original_prompt="本地故障任务",
        prompt="本地故障任务",
        template=None,
        provider_name="local",
        owner_id=None,
    )

    assert result.metadata.provider_used == "offline"
    assert result.metadata.provider_display_name == "离线规则"
    assert result.metadata.fallback_used is True
    assert result.metadata.error_code == code
    assert result.metadata.fallback_reason == reason
    assert result.metadata.recovery_action == action
    assert result.analysis.optimized_prompt


@pytest.mark.parametrize("error", [MemoryError("out of memory"), TimeoutError("runner timeout")])
def test_local_runner_resource_errors_fall_back(tmp_path: Path, error: BaseException) -> None:
    services = build_services(tmp_path, FailingLocalRunner(error))

    result = services.optimization.optimize(
        original_prompt="资源故障任务",
        prompt="资源故障任务",
        template=None,
        provider_name="local",
        owner_id=None,
    )

    assert result.metadata.fallback_used is True
    assert result.metadata.fallback_reason in {"out_of_memory", "timeout"}
    assert result.metadata.recovery_action in {"free_memory", "retry"}


def test_local_stream_timeout_falls_back_with_recovery_metadata(tmp_path: Path) -> None:
    services = build_services(tmp_path, FailingLocalRunner(TimeoutError("runner timeout")))

    events = list(
        services.optimization.stream(
            original_prompt="流式超时任务",
            prompt="流式超时任务",
            template=None,
            provider_name="local",
            owner_id=None,
            request_id="rc150-local-timeout",
        )
    )

    fallback = next(event.data for event in events if event.event == "fallback")
    assert isinstance(fallback, OptimizeMetadata)
    assert fallback.error_code == "LOCAL_MODEL_TIMEOUT"
    assert fallback.fallback_reason == "timeout"
    assert fallback.recovery_action == "retry"
    assert events[-1].event == "completed"


def test_local_generic_runtime_error_is_not_silently_downgraded(tmp_path: Path) -> None:
    services = build_services(tmp_path, FailingLocalRunner(RuntimeError("runner bug")))

    with pytest.raises(RuntimeError, match="runner bug"):
        services.optimization.optimize(
            original_prompt="本地异常任务",
            prompt="本地异常任务",
            template=None,
            provider_name="local",
            owner_id=None,
        )


def test_unconfigured_local_runner_is_reported_as_not_installed(tmp_path: Path) -> None:
    services = build_services(tmp_path, UnavailableLocalRunner())

    result = services.optimization.optimize(
        original_prompt="未安装任务",
        prompt="未安装任务",
        template=None,
        provider_name="local",
        owner_id=None,
    )

    assert result.metadata.error_code == "LOCAL_MODEL_NOT_INSTALLED"
    assert result.metadata.fallback_reason == "not_installed"
    assert result.metadata.recovery_action == "install"
