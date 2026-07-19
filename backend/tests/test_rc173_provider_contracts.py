from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass

import httpx
import pytest

from prompt_optimizer.providers import (
    AnthropicMessagesAdapter,
    AzureOpenAIAdapter,
    BedrockConverseAdapter,
    GeminiAdapter,
    LocalModelProvider,
    ModelProvider,
    ModelRequest,
    OpenAICompatibleAdapter,
    OpenAIResponsesAdapter,
    ProviderConfig,
    ProviderEventType,
    VertexAIAdapter,
)
from prompt_optimizer.providers.local import LocalRunnerHealth
from prompt_optimizer.providers.offline import OfflineRuleProvider

# RC ID: RC-173. Shared MockTransport contracts never call a real Provider.

MOCK_SECRET = "contract-secret-value"
SAFE_PROMPT = "safe contract prompt"
SECRET_HEADERS = {
    "authorization",
    "api-key",
    "x-api-key",
    "x-goog-api-key",
}


class SecretFreeRecording:
    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        body = request.read()
        payload = json.loads(body.decode("utf-8"))
        self.requests.append(
            {
                "method": request.method,
                "url": str(request.url),
                "headers": {
                    key: "[REDACTED]"
                    if key.lower() in SECRET_HEADERS
                    else value
                    for key, value in request.headers.items()
                },
                "body": payload,
            }
        )
        if payload.get("stream") is True or ":streamGenerateContent" in request.url.path:
            return self._stream_response(request)
        if request.url.path.endswith("/responses"):
            return httpx.Response(200, json={"output_text": "contract optimized"})
        if request.url.path.endswith("/messages"):
            return httpx.Response(
                200,
                json={"content": [{"type": "text", "text": "contract optimized"}]},
            )
        if request.url.path.endswith("/converse"):
            return httpx.Response(
                200,
                json={"output": {"message": {"content": [{"text": "contract optimized"}]}}},
            )
        if ":generateContent" in request.url.path:
            return httpx.Response(
                200,
                json={"candidates": [{"content": {"parts": [{"text": "contract optimized"}]}}]},
            )
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "contract optimized"}}]},
        )

    @staticmethod
    def _stream_response(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/responses"):
            content = (
                'event: response.output_text.delta\n'
                'data: {"type":"response.output_text.delta","delta":"contract"}\n'
                'data: {"type":"response.output_text.delta","delta":" stream"}\n'
            )
        elif request.url.path.endswith("/messages"):
            content = (
                'event: content_block_delta\n'
                'data: {"type":"content_block_delta","delta":'
                '{"type":"text_delta","text":"contract"}}\n'
                'data: {"type":"message_stop"}\n'
            )
        elif ":streamGenerateContent" in request.url.path:
            content = (
                'data: {"candidates":[{"content":{"parts":[{"text":"contract"}]}}]}\n'
            )
        else:
            content = (
                'data: {"choices":[{"delta":{"content":"contract"}}]}\n'
                'data: {"choices":[{"delta":{"content":" stream"}}]}\n'
                "data: [DONE]\n"
            )
        return httpx.Response(200, text=content)

    def snapshot(self) -> str:
        return json.dumps(self.requests, ensure_ascii=False, sort_keys=True)


def _config(name: str, **overrides: object) -> ProviderConfig:
    values: dict[str, object] = {
        "name": name,
        "base_url": "https://mock.invalid/v1",
        "api_key": MOCK_SECRET,
        "model": "contract-model",
        "authorized": True,
        "max_retries": 0,
        "rate_limit_per_minute": 100,
    }
    values.update(overrides)
    return ProviderConfig(**values)  # type: ignore[arg-type]


@dataclass(frozen=True)
class RemoteCase:
    name: str
    factory: Callable[[httpx.Client], ModelProvider]


def _bedrock_signer(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes,
) -> dict[str, str]:
    return {**headers, "Authorization": "AWS4-HMAC-SHA256 mock"}


def _remote_cases() -> tuple[RemoteCase, ...]:
    return (
        RemoteCase(
            "openai-chat",
            lambda client: OpenAICompatibleAdapter(_config("openai"), client=client),
        ),
        RemoteCase(
            "openai-responses",
            lambda client: OpenAIResponsesAdapter(
                _config("openai", api_protocol="responses"), client=client
            ),
        ),
        RemoteCase(
            "gemini",
            lambda client: GeminiAdapter(
                _config("gemini", api_protocol="gemini"), client=client
            ),
        ),
        RemoteCase(
            "anthropic",
            lambda client: AnthropicMessagesAdapter(
                _config("anthropic", api_protocol="anthropic"), client=client
            ),
        ),
        RemoteCase(
            "azure",
            lambda client: AzureOpenAIAdapter(
                _config(
                    "azure",
                    api_protocol="azure_openai",
                    deployment="contract-deployment",
                    api_version="2024-10-21",
                ),
                client=client,
            ),
        ),
        RemoteCase(
            "vertex",
            lambda client: VertexAIAdapter(
                _config(
                    "vertex",
                    api_protocol="vertex",
                    project_id="contract-project",
                    region="us-central1",
                ),
                client=client,
            ),
        ),
        RemoteCase(
            "bedrock",
            lambda client: BedrockConverseAdapter(
                _config(
                    "bedrock",
                    api_protocol="bedrock",
                    credential_mode="aws_sigv4",
                    region="us-east-1",
                ),
                client=client,
                signer=_bedrock_signer,
            ),
        ),
    )


@pytest.mark.parametrize("case", _remote_cases(), ids=lambda case: case.name)
def test_remote_provider_contract_uses_secret_free_recording(case: RemoteCase) -> None:
    recording = SecretFreeRecording()
    client = httpx.Client(transport=httpx.MockTransport(recording.handler))
    provider = case.factory(client)

    assert isinstance(provider, ModelProvider)
    response = provider.optimize(ModelRequest(prompt=SAFE_PROMPT))

    assert response.provider_used == provider.name
    assert response.analysis.optimized_prompt == "contract optimized"
    assert len(recording.requests) == 1
    assert MOCK_SECRET not in recording.snapshot()


@pytest.mark.parametrize("case", _remote_cases(), ids=lambda case: case.name)
def test_streaming_provider_contract_emits_shared_events(case: RemoteCase) -> None:
    recording = SecretFreeRecording()
    client = httpx.Client(transport=httpx.MockTransport(recording.handler))
    provider = case.factory(client)
    if not provider.capabilities.streaming:
        pytest.skip("provider does not advertise streaming")

    events = list(provider.stream(ModelRequest(prompt=SAFE_PROMPT)))

    assert [event.type for event in events][0] == ProviderEventType.STARTED
    assert [event.type for event in events][-1] == ProviderEventType.COMPLETED
    assert any(event.type == ProviderEventType.DELTA and event.text for event in events)
    assert MOCK_SECRET not in recording.snapshot()


class ReadyRunner:
    def health(self) -> LocalRunnerHealth:
        return LocalRunnerHealth(True, model_id="local-contract-model", status=None)

    def generate(self, request: ModelRequest) -> str:
        return "local contract optimized"

    def stream(self, request: ModelRequest) -> Iterator[str]:
        yield "local contract"
        yield " optimized"


@pytest.mark.parametrize(
    "provider",
    [OfflineRuleProvider(), LocalModelProvider(ReadyRunner())],
    ids=["offline", "local"],
)
def test_local_and_offline_provider_contract(provider: ModelProvider) -> None:
    assert isinstance(provider, ModelProvider)
    response = provider.optimize(ModelRequest(prompt=SAFE_PROMPT))
    events = list(provider.stream(ModelRequest(prompt=SAFE_PROMPT)))

    assert response.provider_used == provider.name
    assert response.analysis.optimized_prompt
    assert [event.type for event in events][0] == ProviderEventType.STARTED
    assert [event.type for event in events][-1] == ProviderEventType.COMPLETED
