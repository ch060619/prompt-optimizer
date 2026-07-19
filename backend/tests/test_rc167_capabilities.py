from __future__ import annotations

from types import SimpleNamespace

from backend.rabbit_code.agent import AgentCore, AgentEventType

from prompt_optimizer.providers import (
    CAPABILITY_MATRIX,
    CapabilitySnapshot,
    ModelRequest,
    ProviderCapabilities,
    ProviderCapabilityResolver,
    ProviderEvent,
    ProviderEventType,
)
from prompt_optimizer.providers.anthropic import AnthropicMessagesAdapter
from prompt_optimizer.providers.gemini import GeminiAdapter
from prompt_optimizer.providers.hosted import (
    AzureOpenAIAdapter,
    BedrockConverseAdapter,
    VertexAIAdapter,
)
from prompt_optimizer.providers.openai import OpenAICompatibleAdapter
from prompt_optimizer.providers.responses import OpenAIResponsesAdapter

# RC ID: RC-167. Verify capability schema, probe overrides, cache expiry, and feature gating.


def test_capability_resolver_caches_probe_results_until_ttl() -> None:
    now = [100.0]
    calls = 0

    def probe() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"tool_use": False, "context_length": 4096}

    provider = SimpleNamespace(
        name="anthropic",
        model="claude-test",
        capabilities=ProviderCapabilities(streaming=True, tools=True),
    )
    resolver = ProviderCapabilityResolver(ttl_seconds=10, clock=lambda: now[0])

    first = resolver.resolve(provider, probe=probe)
    cached = resolver.resolve(provider, probe=probe)
    assert isinstance(first, CapabilitySnapshot)
    assert first.schema_version == "v1"
    assert first.source == "probe"
    assert first.capabilities.tools is False
    assert first.capabilities.context_length == 4096
    assert cached is first
    assert calls == 1

    now[0] = 110.0
    refreshed = resolver.resolve(provider, probe=probe)
    assert refreshed is not first
    assert calls == 2


def test_probe_failure_keeps_static_contract_and_records_safe_error_type() -> None:
    provider = SimpleNamespace(
        name="openai",
        capabilities=ProviderCapabilities(streaming=True, tools=True),
    )
    snapshot = ProviderCapabilityResolver().resolve(
        provider,
        probe=lambda: (_ for _ in ()).throw(RuntimeError("secret request detail")),
    )

    assert snapshot.source == "static"
    assert snapshot.capabilities.tools is True
    assert snapshot.probe_error == "RuntimeError"
    assert "secret" not in str(snapshot.as_dict())


def test_adapter_capability_matrix_matches_static_declarations() -> None:
    assert OpenAICompatibleAdapter.capabilities == CAPABILITY_MATRIX["chat_completions"]
    assert OpenAIResponsesAdapter.capabilities == CAPABILITY_MATRIX["responses"]
    assert GeminiAdapter.capabilities == CAPABILITY_MATRIX["gemini"]
    assert AnthropicMessagesAdapter.capabilities == CAPABILITY_MATRIX["anthropic"]
    assert AzureOpenAIAdapter.capabilities == CAPABILITY_MATRIX["azure_openai"]
    assert VertexAIAdapter.capabilities == CAPABILITY_MATRIX["vertex"]
    assert BedrockConverseAdapter.capabilities == CAPABILITY_MATRIX["bedrock"]


class ToollessProvider:
    name = "tool-less"
    capabilities = ProviderCapabilities(streaming=True, tools=False)

    def __init__(self) -> None:
        self.seen_request: ModelRequest | None = None

    def optimize(self, request: ModelRequest) -> object:
        raise AssertionError("stream path should be used")

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        self.seen_request = request
        yield ProviderEvent(ProviderEventType.STARTED)
        yield ProviderEvent(ProviderEventType.DELTA, text="output")
        yield ProviderEvent(ProviderEventType.COMPLETED)


def test_agent_disables_optional_tools_from_unsupported_provider() -> None:
    provider = ToollessProvider()
    events = list(
        AgentCore(provider).stream(
            ModelRequest(
                prompt="test",
                tools=({"type": "function", "function": {"name": "noop"}},),
            )
        )
    )

    assert events[-1].type is AgentEventType.COMPLETED
    assert provider.seen_request is not None
    assert provider.seen_request.tools == ()


def test_agent_rejects_required_structured_output_when_unsupported() -> None:
    provider = ToollessProvider()
    events = list(
        AgentCore(provider).stream(
            ModelRequest(prompt="test", response_format={"type": "json_object"})
        )
    )

    assert events[-1].type is AgentEventType.FAILED
    assert "structured_output" in (events[-1].text or "")
    assert provider.seen_request is None
