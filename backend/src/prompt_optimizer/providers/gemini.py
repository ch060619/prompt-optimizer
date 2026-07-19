from __future__ import annotations

import json
from typing import Any

import httpx

from prompt_optimizer.providers.base import (
    ModelRequest,
    ProviderCapabilities,
    ToolCall,
    raise_provider_http_error,
)
from prompt_optimizer.providers.openai import OpenAICompatibleAdapter

# RC ID: RC-162. Implement the native Gemini generateContent protocol.


class GeminiAdapter(OpenAICompatibleAdapter):
    capabilities = ProviderCapabilities(
        streaming=True,
        tools=True,
        structured_output=True,
    )
    display_name = "Google Gemini"

    def _endpoint_url(self, *, stream: bool = False) -> str:
        if not self.config.base_url or not self.config.model:
            raise RuntimeError(f"{self.name} 缺少 base_url、api_key 或 model 配置。")
        base_url = self.config.base_url.rstrip("/")
        if base_url.endswith(":generateContent") or base_url.endswith(":streamGenerateContent"):
            return base_url
        action = ":streamGenerateContent" if stream else ":generateContent"
        return f"{base_url}/models/{self.config.model}{action}"

    def _headers(self, request: ModelRequest) -> dict[str, str]:
        return {
            "x-goog-api-key": self.config.api_key or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _payload(self, request: ModelRequest, *, stream: bool = False) -> dict[str, object]:
        payload: dict[str, object] = {
            "systemInstruction": {"parts": [{"text": request.system_prompt}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": self._build_prompt(request)}],
                }
            ],
        }
        generation_config: dict[str, object] = {}
        if request.response_format:
            generation_config["responseMimeType"] = "application/json"
            schema = request.response_format.get("json_schema") or request.response_format.get(
                "schema"
            )
            if schema is not None:
                generation_config["responseSchema"] = schema
        if generation_config:
            payload["generationConfig"] = generation_config
        if request.tools:
            payload["tools"] = [
                {"function_declarations": [self._gemini_function(tool) for tool in request.tools]}
            ]
        if request.tool_choice is not None:
            payload["toolConfig"] = {
                "function_calling_config": {"mode": self._tool_mode(request.tool_choice)}
            }
        if request.safety_settings:
            payload["safetySettings"] = list(request.safety_settings)
        return payload

    @staticmethod
    def _gemini_function(tool: dict[str, Any]) -> dict[str, Any]:
        function = tool.get("function")
        return function if isinstance(function, dict) else tool

    @staticmethod
    def _tool_mode(choice: str | dict[str, Any]) -> str:
        if isinstance(choice, dict):
            choice = str(choice.get("mode", "AUTO"))
        return choice.upper() if choice.upper() in {"AUTO", "ANY", "NONE"} else "AUTO"

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        raise_provider_http_error(response, "Gemini")

    @staticmethod
    def _extract_message(payload: object) -> tuple[str, tuple[ToolCall, ...]]:
        if not isinstance(payload, dict):
            raise RuntimeError("Gemini 响应不是 JSON 对象。")
        candidates = payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            feedback = payload.get("promptFeedback")
            raise RuntimeError(f"Gemini 未返回候选内容：{feedback or 'unknown'}")
        content = candidates[0].get("content") if isinstance(candidates[0], dict) else None
        parts = content.get("parts") if isinstance(content, dict) else None
        if not isinstance(parts, list):
            raise RuntimeError("Gemini 响应缺少 parts。")
        texts: list[str] = []
        calls: list[ToolCall] = []
        for index, part in enumerate(parts):
            if not isinstance(part, dict):
                continue
            if isinstance(part.get("text"), str):
                texts.append(part["text"])
            function_call = part.get("functionCall")
            if isinstance(function_call, dict):
                name = function_call.get("name")
                args = function_call.get("args", {})
                if isinstance(name, str):
                    calls.append(ToolCall(f"gemini-call-{index}", name, json.dumps(args)))
        if not texts and not calls:
            raise RuntimeError("Gemini 响应没有文本或工具调用。")
        return "".join(texts), tuple(calls)

    @staticmethod
    def _extract_stream_event(
        line: str,
    ) -> tuple[str | None, tuple[ToolCall, ...]]:
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("event:"):
            return None, ()
        if clean_line.startswith("data: "):
            clean_line = clean_line.removeprefix("data: ").strip()
        try:
            payload = json.loads(clean_line)
        except json.JSONDecodeError as exc:
            raise RuntimeError("无法解析 Gemini 流式响应。") from exc
        return GeminiAdapter._extract_message(payload)
