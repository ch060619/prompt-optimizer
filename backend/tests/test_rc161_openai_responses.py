from __future__ import annotations

import httpx

from prompt_optimizer.providers import (
    ModelRequest,
    OpenAICompatibleAdapter,
    OpenAIResponsesAdapter,
    ProviderConfig,
    ProviderEventType,
    ProviderRegistry,
)

# RC ID: RC-161. Verify independent OpenAI Responses request and event contracts.


def _config() -> ProviderConfig:
    return ProviderConfig(
        name="openai",
        base_url="https://api.openai.test/v1",
        api_key="test-key",
        model="gpt-response-test",
        api_protocol="responses",
        max_retries=0,
    )


def test_responses_adapter_does_not_send_chat_messages_or_chat_tool_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/responses"
        body = request.read()
        assert b"messages" not in body
        payload = httpx.Response(200, content=body).json()
        assert payload["instructions"] == "system instruction"
        assert payload["input"][0]["content"][0]["type"] == "input_text"
        assert payload["tools"][0]["name"] == "lookup_release"
        assert "function" not in payload["tools"][0]
        assert payload["text"]["format"]["type"] == "json_schema"
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "目标：整理版本。"}],
                    },
                    {
                        "type": "function_call",
                        "call_id": "call-response-1",
                        "name": "lookup_release",
                        "arguments": '{"version":"3.0"}',
                    },
                ]
            },
        )

    provider = OpenAIResponsesAdapter(
        _config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    response = provider.optimize(
        ModelRequest(
            prompt="整理版本",
            system_prompt="system instruction",
            tools=(
                {
                    "type": "function",
                    "function": {
                        "name": "lookup_release",
                        "description": "Look up a release.",
                        "parameters": {"type": "object"},
                    },
                },
            ),
            response_format={"type": "json_schema", "name": "release"},
        )
    )

    assert response.analysis.optimized_prompt == "目标：整理版本。"
    assert response.tool_calls[0].id == "call-response-1"
    assert provider.capabilities.structured_output is True


def test_responses_adapter_parses_text_delta_and_function_call_done_event() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=(
                'event: response.output_text.delta\n'
                'data: {"type":"response.output_text.delta","delta":"目标："}\n\n'
                'event: response.function_call_arguments.done\n'
                'data: {"type":"response.function_call_arguments.done",'
                '"call_id":"call-response-2","name":"lookup_release",'
                '"arguments":"{\\"version\\":\\"3.0\\"}"}\n\n'
                'event: response.completed\n'
                'data: {"type":"response.completed"}\n\n'
            ),
        )

    provider = OpenAIResponsesAdapter(
        _config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    events = list(provider.stream(ModelRequest(prompt="流式整理")))

    assert [event.type for event in events] == [
        ProviderEventType.STARTED,
        ProviderEventType.DELTA,
        ProviderEventType.DELTA,
        ProviderEventType.COMPLETED,
    ]
    assert events[1].text == "目标："
    assert events[2].tool_calls[0].name == "lookup_release"


def test_registry_selects_responses_only_when_explicitly_configured(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    for suffix, value in {
        "BASE_URL": "https://api.openai.test/v1",
        "API_KEY": "test-key",
        "MODEL": "gpt-response-test",
        "AUTHORIZED": "true",
        "API_PROTOCOL": "responses",
    }.items():
        monkeypatch.setenv(f"RABBIT_CODE_OPENAI_{suffix}", value)

    responses_provider = ProviderRegistry().get("openai")
    assert isinstance(responses_provider, OpenAIResponsesAdapter)

    monkeypatch.setenv("RABBIT_CODE_OPENAI_API_PROTOCOL", "chat_completions")
    chat_provider = ProviderRegistry().get("openai")
    assert isinstance(chat_provider, OpenAICompatibleAdapter)
    assert not isinstance(chat_provider, OpenAIResponsesAdapter)
