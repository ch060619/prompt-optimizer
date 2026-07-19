from __future__ import annotations

import json
from collections.abc import Callable
from urllib.parse import quote

import httpx

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.providers.base import (
    ModelRequest,
    ProviderCapabilities,
    ProviderConfig,
    ToolCall,
)
from prompt_optimizer.providers.gemini import GeminiAdapter
from prompt_optimizer.providers.openai import OpenAICompatibleAdapter

# RC ID: RC-165. Keep Azure, Vertex, and Bedrock authentication/endpoint variants explicit.

RequestSigner = Callable[[str, str, dict[str, str], bytes], dict[str, str]]


class AzureOpenAIAdapter(OpenAICompatibleAdapter):
    display_name = "Azure OpenAI"

    def _endpoint_url(self, *, stream: bool = False) -> str:
        if not self.config.base_url:
            raise RuntimeError(f"{self.name} 缺少 base_url、api_key 或 model 配置。")
        base_url = self.config.base_url.rstrip("/")
        if "/chat/completions" not in base_url:
            deployment = self.config.deployment or self.config.model
            base_url = f"{base_url}/openai/deployments/{quote(deployment or '')}/chat/completions"
        if "api-version=" not in base_url:
            separator = "&" if "?" in base_url else "?"
            base_url += f"{separator}api-version={quote(self.config.api_version or '2024-10-21')}"
        return base_url

    def _headers(self, request: ModelRequest) -> dict[str, str]:
        headers = super()._headers(request)
        headers.pop("Authorization", None)
        headers["api-key"] = self.config.api_key or ""
        return headers


class VertexAIAdapter(GeminiAdapter):
    display_name = "Google Vertex AI"

    def _endpoint_url(self, *, stream: bool = False) -> str:
        if not self.config.base_url or not self.config.model:
            raise RuntimeError(f"{self.name} 缺少 base_url、api_key 或 model 配置。")
        base_url = self.config.base_url.rstrip("/")
        if "/projects/" in base_url and base_url.endswith(
            (":generateContent", ":streamGenerateContent")
        ):
            return base_url
        project = self.config.project_id or self.config.project
        region = self.config.region or "global"
        action = ":streamGenerateContent" if stream else ":generateContent"
        return (
            f"{base_url}/v1/projects/{quote(project or '')}/locations/{quote(region)}"
            f"/publishers/google/models/{quote(self.config.model)}{action}"
        )

    def _headers(self, request: ModelRequest) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key or ''}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }


class BedrockConverseAdapter(OpenAICompatibleAdapter):
    capabilities = ProviderCapabilities(streaming=False, tools=True, token_usage=True)
    display_name = "AWS Bedrock Converse"

    def __init__(
        self,
        config: ProviderConfig,
        analyzer: Analyzer | None = None,
        client: httpx.Client | None = None,
        signer: RequestSigner | None = None,
    ) -> None:
        super().__init__(config, analyzer=analyzer, client=client)
        self.signer = signer

    def _endpoint_url(self, *, stream: bool = False) -> str:
        if not self.config.base_url or not self.config.model:
            raise RuntimeError(f"{self.name} 缺少 base_url、api_key 或 model 配置。")
        base_url = self.config.base_url.rstrip("/")
        if base_url.endswith("/converse"):
            return base_url
        return f"{base_url}/model/{quote(self.config.model)}/converse"

    def _headers(self, request: ModelRequest) -> dict[str, str]:
        return {"Content-Type": "application/json", "Accept": "application/json"}

    def _payload(self, request: ModelRequest, *, stream: bool = False) -> dict[str, object]:
        return {
            "system": [{"text": request.system_prompt}],
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": self._build_prompt(request)}],
                }
            ],
        }

    def _request_model(
        self,
        request: ModelRequest,
    ) -> tuple[str, tuple[ToolCall, ...], dict[str, int] | None]:
        self._check_cancelled(request)
        if self.signer is None:
            raise RuntimeError("Bedrock requires an official AWS SigV4 signer.")
        body = json.dumps(self._payload(request), ensure_ascii=False).encode("utf-8")
        endpoint = self._endpoint_url()
        headers = self.signer("POST", endpoint, self._headers(request), body)
        response = self.client.post(endpoint, headers=headers, content=body)
        self._raise_for_status(response)
        payload = response.json()
        content, tool_calls = self._extract_message(payload)
        return content, tool_calls, self._extract_usage(payload)

    @staticmethod
    def _extract_message(payload: object) -> tuple[str, tuple[ToolCall, ...]]:
        if not isinstance(payload, dict):
            raise RuntimeError("Bedrock 响应不是 JSON 对象。")
        output = payload.get("output")
        message = output.get("message") if isinstance(output, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            raise RuntimeError("Bedrock Converse 响应缺少 content。")
        texts: list[str] = []
        calls: list[ToolCall] = []
        for index, block in enumerate(content):
            if not isinstance(block, dict):
                continue
            if isinstance(block.get("text"), str):
                texts.append(block["text"])
            tool_use = block.get("toolUse")
            if isinstance(tool_use, dict) and isinstance(tool_use.get("name"), str):
                calls.append(
                    ToolCall(
                        str(tool_use.get("toolUseId", f"bedrock-call-{index}")),
                        tool_use["name"],
                        json.dumps(tool_use.get("input", {})),
                    )
                )
        if not texts and not calls:
            raise RuntimeError("Bedrock Converse 响应没有文本或工具调用。")
        return "".join(texts), tuple(calls)

