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

# RC IDs: RC-163, RC-164. Implement the native Anthropic Messages protocol and approved boundary.


class AnthropicMessagesAdapter(OpenAICompatibleAdapter):
    capabilities = ProviderCapabilities(streaming=True, tools=True, token_usage=True)
    display_name = "Anthropic Messages"

    def _endpoint_url(self, *, stream: bool = False) -> str:
        if not self.config.base_url:
            raise RuntimeError(f"{self.name} 缺少 base_url、api_key 或 model 配置。")
        base_url = self.config.base_url.rstrip("/")
        return base_url if base_url.endswith("/messages") else f"{base_url}/messages"

    def _headers(self, request: ModelRequest) -> dict[str, str]:
        headers = {
            "x-api-key": self.config.api_key or "",
            "anthropic-version": self.config.api_version or "2023-06-01",
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if request.request_id else "application/json",
        }
        if self.config.beta_features:
            headers["anthropic-beta"] = ",".join(self.config.beta_features)
        return headers

    def _payload(self, request: ModelRequest, *, stream: bool = False) -> dict[str, object]:
        system_block: dict[str, object] = {"type": "text", "text": request.system_prompt}
        if request.cache_prompt or self.config.prompt_caching:
            system_block["cache_control"] = {"type": "ephemeral"}
        content: list[dict[str, object]] = [
            {"type": "text", "text": self._build_prompt(request)}
        ]
        content.extend(
            {"type": "tool_result", **tool_result} for tool_result in request.tool_results
        )
        payload: dict[str, object] = {
            "model": self.config.model,
            "max_tokens": 4096,
            "system": [system_block],
            "messages": [{"role": "user", "content": content}],
        }
        if stream:
            payload["stream"] = True
        if request.tools:
            payload["tools"] = [self._anthropic_tool(tool) for tool in request.tools]
        if request.tool_choice is not None:
            payload["tool_choice"] = self._tool_choice(request.tool_choice)
        return payload

    @staticmethod
    def _anthropic_tool(tool: dict[str, Any]) -> dict[str, Any]:
        function = tool.get("function")
        if not isinstance(function, dict):
            return tool
        return {
            "name": function.get("name", "tool"),
            "description": function.get("description", ""),
            "input_schema": function.get("parameters", {"type": "object"}),
        }

    @staticmethod
    def _tool_choice(choice: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(choice, dict):
            return choice
        normalized = choice.lower()
        return {"type": normalized if normalized in {"auto", "any", "none"} else "auto"}

    def probe_capabilities(self) -> dict[str, bool]:
        return {
            "tool_use": self.capabilities.tools,
            "prompt_caching": self.config.prompt_caching
            or "prompt-caching" in self.config.beta_features,
            "beta_extensions": bool(self.config.beta_features),
        }

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        raise_provider_http_error(response, "Anthropic")

    @staticmethod
    def _extract_message(payload: object) -> tuple[str, tuple[ToolCall, ...]]:
        if not isinstance(payload, dict):
            raise RuntimeError("Anthropic 响应不是 JSON 对象。")
        content = payload.get("content")
        if not isinstance(content, list):
            raise RuntimeError("Anthropic 响应缺少 content blocks。")
        texts: list[str] = []
        calls: list[ToolCall] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                texts.append(block["text"])
            if block.get("type") == "tool_use":
                call_id = block.get("id")
                name = block.get("name")
                if isinstance(call_id, str) and isinstance(name, str):
                    calls.append(
                        ToolCall(call_id, name, json.dumps(block.get("input", {})))
                    )
        if not texts and not calls:
            raise RuntimeError("Anthropic 响应没有文本或工具调用。")
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
            raise RuntimeError("无法解析 Anthropic 流式响应。") from exc
        if not isinstance(payload, dict):
            return None, ()
        if payload.get("type") == "content_block_delta":
            delta = payload.get("delta")
            if isinstance(delta, dict) and delta.get("type") == "text_delta":
                text = delta.get("text")
                return (text, ()) if isinstance(text, str) else (None, ())
        if payload.get("type") == "content_block_start":
            block = payload.get("content_block")
            if isinstance(block, dict) and block.get("type") == "tool_use":
                call_id = block.get("id")
                name = block.get("name")
                if isinstance(call_id, str) and isinstance(name, str):
                    return None, (ToolCall(call_id, name, json.dumps(block.get("input", {}))),)
        return None, ()
