from __future__ import annotations

import pytest

from prompt_optimizer.providers import (
    ModelRequest,
    ProviderConfig,
    ProviderConnectionTester,
    ProviderEvent,
    ProviderEventType,
)

# RC ID: RC-169. Verify Mock-first connection checks and explicit real-request consent.


def provider_config(*, api_key: str | None = "owned-key") -> ProviderConfig:
    return ProviderConfig(
        name="openai",
        api_key=api_key,
        model="test-model",
        api_protocol="chat_completions",
    )


def test_default_connection_check_is_mock_only_and_staged() -> None:
    result = ProviderConnectionTester().run(provider_config())

    assert result.passed
    assert result.mode == "mock"
    assert result.real_request_sent is False
    assert [step.name for step in result.steps] == [
        "credentials",
        "model",
        "capabilities",
        "first_chunk",
        "tool_call",
    ]
    assert result.cost_warning.startswith("Mock check only")


def test_missing_credential_returns_repair_hint_without_network() -> None:
    result = ProviderConnectionTester().run(provider_config(api_key=None))

    credential_step = result.steps[0]
    assert not result.passed
    assert credential_step.status == "failed"
    assert credential_step.repair_hint


def test_real_mode_requires_confirmation_and_does_not_call_sender_early() -> None:
    calls: list[tuple[ProviderConfig, ModelRequest, int]] = []

    def sender(config: ProviderConfig, request: ModelRequest, limit: int):
        calls.append((config, request, limit))
        yield ProviderEvent(ProviderEventType.STARTED)
        yield ProviderEvent(ProviderEventType.DELTA, text="OK")

    tester = ProviderConnectionTester(real_sender=sender)
    result = tester.run(provider_config(), mode="real", confirmed=False, token_limit=128)

    assert not result.passed
    assert result.real_request_sent is False
    assert result.steps[-1].status == "blocked"
    assert "charges" in result.cost_warning
    assert calls == []


def test_confirmed_real_mode_uses_minimal_request_and_token_limit() -> None:
    calls: list[tuple[ProviderConfig, ModelRequest, int]] = []

    def sender(config: ProviderConfig, request: ModelRequest, limit: int):
        calls.append((config, request, limit))
        yield ProviderEvent(ProviderEventType.STARTED)
        yield ProviderEvent(ProviderEventType.DELTA, text="OK")

    result = ProviderConnectionTester(real_sender=sender).run(
        provider_config(), mode="real", confirmed=True, token_limit=64
    )

    assert result.passed
    assert result.real_request_sent is True
    assert calls and calls[0][1].prompt == "Return exactly OK."
    assert calls[0][1].tools
    assert calls[0][2] == 64


def test_token_limit_is_bounded_before_any_test_request() -> None:
    with pytest.raises(ValueError, match="token_limit"):
        ProviderConnectionTester().run(provider_config(), token_limit=0)
