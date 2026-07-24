from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass

import httpx
import pytest

from prompt_optimizer.providers import (
    AnthropicMessagesAdapter,
    GeminiAdapter,
    ModelRequest,
    OpenAICompatibleAdapter,
    OpenAIResponsesAdapter,
    ProviderConfig,
    ProviderEventType,
    ProviderParameterError,
    ProviderUnauthorizedError,
)

# RC ID: RC-231. Exercise the shared Mock contract across native and compatible adapters.

MOCK_KEY = "contract-secret"


def _tool() -> dict[str, object]:
    return {
        "type": "function",
        "function": {
            "name": "lookup_release",
            "description": "Look up a release.",
            "parameters": {"type": "object", "properties": {"version": {"type": "string"}}},
        },
    }


def _config(name: str, protocol: str = "chat_completions") -> ProviderConfig:
    return ProviderConfig(
        name=name,
        base_url=f"https://{name}.provider.test/v1",
        api_key=MOCK_KEY,
        model="contract-model",
        api_protocol=protocol,  # type: ignore[arg-type]
        max_retries=0,
    )


@dataclass(frozen=True)
class ContractCase:
    name: str
    factory: Callable[[httpx.Client], object]
    path: str
    request_assertion: Callable[[dict[str, object]], None]
    response: dict[str, object]
    stream: str


def _assert_chat_request(payload: dict[str, object]) -> None:
    assert isinstance(payload.get("messages"), list)
    assert payload["tools"] == [_tool()]


def _assert_responses_request(payload: dict[str, object]) -> None:
    assert isinstance(payload.get("instructions"), str)
    assert isinstance(payload.get("input"), list)
    assert payload["tools"][0]["name"] == "lookup_release"  # type: ignore[index]


def _assert_gemini_request(payload: dict[str, object]) -> None:
    assert isinstance(payload.get("contents"), list)
    assert payload["tools"][0]["function_declarations"][0]["name"] == "lookup_release"  # type: ignore[index]


def _assert_anthropic_request(payload: dict[str, object]) -> None:
    assert isinstance(payload.get("messages"), list)
    assert payload["tools"][0]["name"] == "lookup_release"  # type: ignore[index]


def _cases() -> tuple[ContractCase, ...]:
    return (
        ContractCase(
            "openai-chat",
            lambda client: OpenAICompatibleAdapter(_config("openai"), client=client),
            "/v1/chat/completions",
            _assert_chat_request,
            {
                "choices": [
                    {
                        "message": {
                            "content": "contract text",
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "lookup_release",
                                        "arguments": '{"version":"3.0"}',
                                    },
                                }
                            ],
                        }
                    }
                ],
                "future_field": {"ignored": True},
            },
            'data: {"choices":[{"delta":{"content":"contract"},"future":true}]}\n'
            'data: {"choices":[{"delta":{"tool_calls":[{"id":"call-1",'
            '"type":"function","function":{"name":"lookup_release",'
            '"arguments":"{\\"version\\":\\"3.0\\"}"}}]}}]}\n'
            "data: [DONE]\n",
        ),
        ContractCase(
            "openrouter-compatible",
            lambda client: OpenAICompatibleAdapter(_config("openrouter"), client=client),
            "/v1/chat/completions",
            _assert_chat_request,
            {
                "choices": [
                    {
                        "message": {
                            "content": "contract text",
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "lookup_release",
                                        "arguments": '{"version":"3.0"}',
                                    },
                                }
                            ],
                        }
                    }
                ],
                "provider_metadata": {"future": "ignored"},
            },
            'data: {"choices":[{"delta":{"content":"contract"}}]}\n'
            'data: {"choices":[{"delta":{"tool_calls":[{"id":"call-1",'
            '"type":"function","function":{"name":"lookup_release",'
            '"arguments":"{\\"version\\":\\"3.0\\"}"}}]}}]}\n'
            "data: [DONE]\n",
        ),
        ContractCase(
            "openai-responses",
            lambda client: OpenAIResponsesAdapter(
                _config("openai", "responses"), client=client
            ),
            "/v1/responses",
            _assert_responses_request,
            {
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "contract text"}],
                    },
                    {
                        "type": "function_call",
                        "call_id": "call-1",
                        "name": "lookup_release",
                        "arguments": '{"version":"3.0"}',
                    },
                ],
                "future_field": "ignored",
            },
            'event: response.output_text.delta\n'
            'data: {"type":"response.output_text.delta","delta":"contract"}\n\n'
            'event: response.function_call_arguments.done\n'
            'data: {"type":"response.function_call_arguments.done",'
            '"call_id":"call-1","name":"lookup_release",'
            '"arguments":"{\\"version\\":\\"3.0\\"}"}\n\n'
            'event: response.completed\n'
            'data: {"type":"response.completed","future":true}\n\n',
        ),
        ContractCase(
            "gemini",
            lambda client: GeminiAdapter(_config("gemini", "gemini"), client=client),
            "/v1/models/contract-model:generateContent",
            _assert_gemini_request,
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "contract text"},
                                {
                                    "functionCall": {
                                        "name": "lookup_release",
                                        "args": {"version": "3.0"},
                                    }
                                },
                            ]
                        }
                    }
                ],
                "future_field": 1,
            },
            'data: {"candidates":[{"content":{"parts":[{"text":"contract"}]}}]}\n\n'
            'data: {"candidates":[{"content":{"parts":[{"functionCall":'
            '{"name":"lookup_release","args":{"version":"3.0"}}}]}}],'
            '"future":true}\n\n',
        ),
        ContractCase(
            "anthropic",
            lambda client: AnthropicMessagesAdapter(
                _config("anthropic", "anthropic"), client=client
            ),
            "/v1/messages",
            _assert_anthropic_request,
            {
                "content": [
                    {"type": "text", "text": "contract text"},
                    {
                        "type": "tool_use",
                        "id": "toolu-1",
                        "name": "lookup_release",
                        "input": {"version": "3.0"},
                    },
                ],
                "usage": {"input_tokens": 3, "output_tokens": 2, "future": 1},
                "future_field": "ignored",
            },
            'event: content_block_delta\n'
            'data: {"type":"content_block_delta","delta":{"type":"text_delta",'
            '"text":"contract"}}\n\n'
            'event: content_block_start\n'
            'data: {"type":"content_block_start","content_block":{"type":"tool_use",'
            '"id":"toolu-1","name":"lookup_release","input":{}}}\n\n'
            'event: message_stop\n'
            'data: {"type":"message_stop","future":true}\n\n',
        ),
    )


def _client_for(case: ContractCase, *, stream: bool = False) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        expected_path = case.path
        if stream and case.name == "gemini":
            expected_path = case.path.replace(":generateContent", ":streamGenerateContent")
        assert request.url.path == expected_path
        body = request.read()
        assert MOCK_KEY.encode() not in body
        payload = json.loads(body.decode())
        case.request_assertion(payload)
        if stream:
            return httpx.Response(200, text=case.stream)
        return httpx.Response(200, json=case.response)

    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case.name)
def test_shared_contract_covers_requests_tools_streams_and_forward_fields(
    case: ContractCase,
) -> None:
    provider = case.factory(_client_for(case))
    response = provider.optimize(ModelRequest(prompt="contract prompt", tools=(_tool(),)))  # type: ignore[attr-defined]

    assert response.analysis.optimized_prompt == "contract text"  # type: ignore[attr-defined]
    assert response.tool_calls[0].name == "lookup_release"  # type: ignore[attr-defined]

    stream_provider = case.factory(_client_for(case, stream=True))
    events = list(
        stream_provider.stream(  # type: ignore[attr-defined]
            ModelRequest(prompt="contract stream", tools=(_tool(),))
        )
    )
    assert [event.type for event in events] == [
        ProviderEventType.STARTED,
        ProviderEventType.DELTA,
        ProviderEventType.DELTA,
        ProviderEventType.COMPLETED,
    ]
    assert any(event.text for event in events)
    assert any(event.tool_calls for event in events)


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case.name)
@pytest.mark.parametrize(
    ("status", "error_type", "body"),
    [
        (401, "auth", {"error": {"code": "invalid_api_key", "message": "bad key"}}),
        (400, "parameter", {"error": {"code": "invalid_request", "message": "bad input"}}),
    ],
)
def test_shared_contract_maps_common_errors_without_network(
    case: ContractCase,
    status: int,
    error_type: str,
    body: dict[str, object],
) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(status, json=body))
    )
    provider = case.factory(client)
    error_class = {"auth": ProviderUnauthorizedError, "parameter": ProviderParameterError}[
        error_type
    ]

    with pytest.raises(error_class):
        provider.optimize(ModelRequest(prompt="error contract"))  # type: ignore[attr-defined]
