from __future__ import annotations

import json
from typing import Any

from prompt_optimizer.providers.base import ModelRequest, ProviderCapabilities, ToolCall
from prompt_optimizer.providers.openai import OpenAICompatibleAdapter

# RC ID: RC-161. Keep OpenAI Responses API requests and events separate from Chat Completions.


class OpenAIResponsesAdapter(OpenAICompatibleAdapter):
    capabilities = ProviderCapabilities(
        streaming=True,
        tools=True,
        structured_output=True,
    )

    display_name = "OpenAI Responses"

    def _endpoint_url(self, *, stream: bool = False) -> str:
        if not self.config.base_url:
            raise RuntimeError(f"{self.name} 缺少 base_url、api_key 或 model 配置。")
        base_url = self.config.base_url.rstrip("/")
        if base_url.endswith("/responses"):
            return base_url
        if base_url.endswith("/chat/completions"):
            base_url = base_url.removesuffix("/chat/completions")
        return f"{base_url}/responses"

    def _payload(self, request: ModelRequest, *, stream: bool = False) -> dict[str, object]:
        payload: dict[str, object] = {
            "model": self.config.model,
            "instructions": request.system_prompt,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": self._build_prompt(request),
                        }
                    ],
                }
            ],
        }
        if stream:
            payload["stream"] = True
        if request.tools:
            payload["tools"] = [self._response_tool(tool) for tool in request.tools]
        if request.tool_choice is not None:
            payload["tool_choice"] = request.tool_choice
        if request.response_format is not None:
            payload["text"] = {"format": request.response_format}
        return payload

    @staticmethod
    def _response_tool(tool: dict[str, Any]) -> dict[str, Any]:
        if tool.get("type") != "function":
            return tool
        function = tool.get("function")
        if not isinstance(function, dict):
            return tool
        return {"type": "function", **function}

    @staticmethod
    def _extract_message(payload: object) -> tuple[str, tuple[ToolCall, ...]]:
        if not isinstance(payload, dict):
            raise RuntimeError("模型响应不是 JSON 对象。")
        output_text = payload.get("output_text")
        if isinstance(output_text, str):
            return output_text, OpenAIResponsesAdapter._extract_output_tool_calls(
                payload.get("output")
            )
        output = payload.get("output")
        if not isinstance(output, list):
            raise RuntimeError("无法解析 Responses API 响应。")
        texts: list[str] = []
        tool_calls: list[ToolCall] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "message":
                content = item.get("content")
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and isinstance(part.get("text"), str):
                            texts.append(part["text"])
            elif item.get("type") == "function_call":
                call_id = item.get("call_id") or item.get("id")
                name = item.get("name")
                arguments = item.get("arguments")
                if (
                    isinstance(call_id, str)
                    and isinstance(name, str)
                    and isinstance(arguments, str)
                ):
                    tool_calls.append(ToolCall(call_id, name, arguments))
        if not texts and not tool_calls:
            raise RuntimeError("无法解析 Responses API 响应。")
        return "".join(texts), tuple(tool_calls)

    @staticmethod
    def _extract_output_tool_calls(value: object) -> tuple[ToolCall, ...]:
        if not isinstance(value, list):
            return ()
        calls: list[ToolCall] = []
        for item in value:
            if not isinstance(item, dict) or item.get("type") != "function_call":
                continue
            call_id = item.get("call_id") or item.get("id")
            name = item.get("name")
            arguments = item.get("arguments")
            if isinstance(call_id, str) and isinstance(name, str) and isinstance(arguments, str):
                calls.append(ToolCall(call_id, name, arguments))
        return tuple(calls)

    @staticmethod
    def _extract_stream_event(
        line: str,
    ) -> tuple[str | None, tuple[ToolCall, ...]]:
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("event:"):
            return None, ()
        if clean_line.startswith("data: "):
            clean_line = clean_line.removeprefix("data: ").strip()
        if clean_line == "[DONE]":
            return None, ()
        try:
            payload = json.loads(clean_line)
        except json.JSONDecodeError as exc:
            raise RuntimeError("无法解析 Responses API 流式响应。") from exc
        if not isinstance(payload, dict):
            return None, ()
        event_type = payload.get("type")
        if event_type == "response.output_text.delta" and isinstance(payload.get("delta"), str):
            return payload["delta"], ()
        if event_type == "response.function_call_arguments.done":
            call_id = payload.get("call_id") or payload.get("item_id")
            name = payload.get("name")
            arguments = payload.get("arguments")
            if isinstance(call_id, str) and isinstance(name, str) and isinstance(arguments, str):
                return None, (ToolCall(call_id, name, arguments),)
        return None, ()
