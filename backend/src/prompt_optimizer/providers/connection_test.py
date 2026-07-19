from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Literal

from prompt_optimizer.providers.base import (
    ModelRequest,
    ProviderConfig,
    ProviderEvent,
    ProviderEventType,
)
from prompt_optimizer.providers.capabilities import CAPABILITY_MATRIX, ProviderCapabilityResolver

# RC ID: RC-169. Keep connection checks Mock-first and require explicit real-request confirmation.

ConnectionMode = Literal["mock", "real"]
ConnectionStepStatus = Literal["passed", "failed", "skipped", "blocked"]
RealConnectionSender = Callable[
    [ProviderConfig, ModelRequest, int],
    Iterable[ProviderEvent],
]


@dataclass(frozen=True)
class ConnectionTestStep:
    name: str
    status: ConnectionStepStatus
    message: str
    repair_hint: str | None = None


@dataclass(frozen=True)
class ConnectionTestResult:
    provider: str
    model: str | None
    mode: ConnectionMode
    steps: tuple[ConnectionTestStep, ...]
    capabilities: dict[str, object]
    token_limit: int
    cost_warning: str
    real_request_sent: bool = False

    @property
    def passed(self) -> bool:
        return all(step.status in {"passed", "skipped"} for step in self.steps)


class ProviderConnectionTester:
    def __init__(
        self,
        *,
        capability_resolver: ProviderCapabilityResolver | None = None,
        real_sender: RealConnectionSender | None = None,
    ) -> None:
        self.capability_resolver = capability_resolver or ProviderCapabilityResolver()
        self.real_sender = real_sender

    def run(
        self,
        config: ProviderConfig,
        *,
        mode: ConnectionMode = "mock",
        confirmed: bool = False,
        token_limit: int = 512,
    ) -> ConnectionTestResult:
        if not 1 <= token_limit <= 100_000:
            raise ValueError("token_limit must be between 1 and 100000")
        snapshot = self.capability_resolver.resolve(
            SimpleNamespace(
                name=config.name,
                model=config.model,
                capabilities=CAPABILITY_MATRIX.get(
                    config.api_protocol,
                    CAPABILITY_MATRIX["chat_completions"],
                ),
            )
        )
        steps: list[ConnectionTestStep] = [
            self._credentials_step(config),
            self._model_step(config),
            ConnectionTestStep(
                "capabilities",
                "passed",
                f"Capability schema {snapshot.schema_version} resolved from {snapshot.source}.",
            ),
        ]
        cost_warning = (
            "Mock check only; no external request and no Provider charge."
            if mode == "mock"
            else f"Real request may incur Provider charges; token limit is {token_limit}."
        )
        base_result = self._result(
            config,
            mode,
            steps,
            snapshot.as_dict(),
            token_limit,
            cost_warning,
        )
        if mode == "mock":
            return self._mock_steps(
                base_result,
                snapshot.capabilities.streaming,
                snapshot.capabilities.tools,
            )
        if not base_result.passed:
            return base_result
        if not confirmed:
            return self._result(
                config,
                mode,
                [
                    *steps,
                    ConnectionTestStep(
                        "confirmation",
                        "blocked",
                        "Explicit confirmation is required before a real request.",
                        "Confirm the Provider cost warning and use an API credential you own.",
                    ),
                ],
                snapshot.as_dict(),
                token_limit,
                cost_warning,
            )
        if self.real_sender is None:
            return self._result(
                config,
                mode,
                [
                    *steps,
                    ConnectionTestStep(
                        "real_request",
                        "failed",
                        "No real-request sender is configured.",
                        "Use the official Provider adapter through an explicit manual action.",
                    ),
                ],
                snapshot.as_dict(),
                token_limit,
                cost_warning,
            )
        try:
            tools = (
                (
                    {
                        "type": "function",
                        "function": {
                            "name": "rabbit_code_connection_probe",
                            "description": (
                                "Connection contract probe; do not execute side effects."
                            ),
                            "parameters": {"type": "object", "properties": {}},
                        },
                    },
                )
                if snapshot.capabilities.tools
                else ()
            )
            events = iter(
                self.real_sender(
                    config,
                    ModelRequest(
                        prompt="Return exactly OK.",
                        request_id="rabbit-code-connection-test",
                        tools=tools,
                    ),
                    token_limit,
                )
            )
            first_event = next(events)
        except Exception:
            return self._result(
                config,
                mode,
                [
                    *steps,
                    ConnectionTestStep(
                        "first_chunk",
                        "failed",
                        "The minimum real request failed before the first event.",
                        "Check the credential, endpoint, model, region, and Provider status.",
                    ),
                ],
                snapshot.as_dict(),
                token_limit,
                cost_warning,
            )
        first_status: ConnectionStepStatus = (
            "passed"
            if first_event.type in {ProviderEventType.STARTED, ProviderEventType.DELTA}
            else "failed"
        )
        return self._result(
            config,
            mode,
            [
                *steps,
                ConnectionTestStep(
                    "first_chunk",
                    first_status,
                    (
                        "Received the first Provider event."
                        if first_status == "passed"
                        else "Provider returned no usable first event."
                    ),
                    (
                        None
                        if first_status == "passed"
                        else "Retry with the same model or inspect the Provider error."
                    ),
                ),
                ConnectionTestStep(
                    "tool_call",
                    "passed" if snapshot.capabilities.tools else "skipped",
                    (
                        "Tool schema contract is available."
                        if snapshot.capabilities.tools
                        else "Provider does not advertise tools."
                    ),
                ),
            ],
            snapshot.as_dict(),
            token_limit,
            cost_warning,
            real_request_sent=True,
        )

    def _mock_steps(
        self,
        result: ConnectionTestResult,
        streaming: bool,
        tools: bool,
    ) -> ConnectionTestResult:
        return ConnectionTestResult(
            provider=result.provider,
            model=result.model,
            mode=result.mode,
            steps=(
                *result.steps,
                ConnectionTestStep(
                    "first_chunk",
                    "passed" if streaming else "skipped",
                    (
                        "Mock stream produced a first event."
                        if streaming
                        else "Streaming is not advertised; non-stream request remains available."
                    ),
                ),
                ConnectionTestStep(
                    "tool_call",
                    "passed" if tools else "skipped",
                    (
                        "Mock tool schema contract is available."
                        if tools
                        else "Provider does not advertise tools."
                    ),
                ),
            ),
            capabilities=result.capabilities,
            token_limit=result.token_limit,
            cost_warning=result.cost_warning,
        )

    @staticmethod
    def _credentials_step(config: ProviderConfig) -> ConnectionTestStep:
        if config.name.lower() in {"ollama", "lmstudio", "offline", "local"}:
            return ConnectionTestStep(
                "credentials",
                "passed",
                "Local or offline route needs no remote API key.",
            )
        if config.api_key:
            return ConnectionTestStep(
                "credentials",
                "passed",
                "Provider credential reference is configured.",
            )
        return ConnectionTestStep(
            "credentials",
            "failed",
            "No Provider credential is configured.",
            "Add the Provider API key or approved credential reference.",
        )

    @staticmethod
    def _model_step(config: ProviderConfig) -> ConnectionTestStep:
        if config.model:
            return ConnectionTestStep("model", "passed", "A model ID is configured.")
        return ConnectionTestStep(
            "model",
            "failed",
            "No model ID is configured.",
            "Discover models or enter a model ID manually.",
        )

    @staticmethod
    def _result(
        config: ProviderConfig,
        mode: ConnectionMode,
        steps: list[ConnectionTestStep],
        capabilities: dict[str, object],
        token_limit: int,
        cost_warning: str,
        *,
        real_request_sent: bool = False,
    ) -> ConnectionTestResult:
        return ConnectionTestResult(
            provider=config.name,
            model=config.model,
            mode=mode,
            steps=tuple(steps),
            capabilities=capabilities,
            token_limit=token_limit,
            cost_warning=cost_warning,
            real_request_sent=real_request_sent,
        )
