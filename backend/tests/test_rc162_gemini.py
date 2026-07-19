from __future__ import annotations

import httpx

from prompt_optimizer.providers import (
    GeminiAdapter,
    ModelRequest,
    ProviderConfig,
    ProviderEventType,
    ProviderRegistry,
)

# RC ID: RC-162. Verify native Gemini request, stream, tools, safety, and errors.


def _config() -> ProviderConfig:
    return ProviderConfig(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        api_key="gemini-key",
        model="gemini-2.0-flash",
        api_protocol="gemini",
        max_retries=0,
    )


def _tool() -> dict[str, object]:
    return {
        "type": "function",
        "function": {
            "name": "lookup_release",
            "description": "Look up a release.",
            "parameters": {"type": "object", "properties": {"version": {"type": "string"}}},
        },
    }


def test_gemini_generate_content_uses_native_parts_tools_and_safety() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1beta/models/gemini-2.0-flash:generateContent"
        assert request.headers["x-goog-api-key"] == "gemini-key"
        body = request.read()
        assert b"messages" not in body
        payload = httpx.Response(200, content=body).json()
        assert payload["systemInstruction"]["parts"][0]["text"] == "Gemini system"
        assert payload["contents"][0]["parts"][0]["text"]
        assert payload["tools"][0]["function_declarations"][0]["name"] == "lookup_release"
        assert payload["safetySettings"][0]["category"] == "HARM_CATEGORY_HARASSMENT"
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "目标：整理版本。"},
                                {
                                    "functionCall": {
                                        "name": "lookup_release",
                                        "args": {"version": "3.0"},
                                    }
                                },
                            ]
                        }
                    }
                ]
            },
        )

    provider = GeminiAdapter(
        _config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    response = provider.optimize(
        ModelRequest(
            prompt="整理版本",
            system_prompt="Gemini system",
            tools=(_tool(),),
            safety_settings=(
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH",
                },
            ),
        )
    )

    assert response.analysis.optimized_prompt == "目标：整理版本。"
    assert response.tool_calls[0].name == "lookup_release"


def test_gemini_stream_generate_content_parses_text_and_function_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1beta/models/gemini-2.0-flash:streamGenerateContent"
        return httpx.Response(
            200,
            content=(
                'data: {"candidates":[{"content":{"parts":[{"text":"目标："}]}}]}\n\n'
                'data: {"candidates":[{"content":{"parts":[{"functionCall":'
                '{"name":"lookup_release","args":{"version":"3.0"}}}]}}]}\n\n'
            ),
        )

    provider = GeminiAdapter(
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


def test_registry_selects_gemini_adapter_without_openai_headers(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    for suffix, value in {
        "BASE_URL": "https://generativelanguage.googleapis.com/v1beta",
        "API_KEY": "gemini-key",
        "MODEL": "gemini-2.0-flash",
        "AUTHORIZED": "true",
    }.items():
        monkeypatch.setenv(f"RABBIT_CODE_GEMINI_{suffix}", value)

    provider = ProviderRegistry().get("gemini")

    assert isinstance(provider, GeminiAdapter)
    assert provider.config.api_protocol == "gemini"  # type: ignore[attr-defined]
