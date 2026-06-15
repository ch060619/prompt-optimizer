from __future__ import annotations

import json
import time
from collections.abc import Iterator
from time import perf_counter

import httpx

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.providers.base import (
    ModelRequest,
    ModelResponse,
    ProviderConfig,
    ProviderRateLimitError,
    ProviderTimeoutError,
)


class HttpChatProvider:
    def __init__(
        self,
        config: ProviderConfig,
        analyzer: Analyzer | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.config = config
        self.name = config.name
        self.analyzer = analyzer or Analyzer()
        self.client = client or httpx.Client(timeout=config.timeout_seconds)
        self._last_calls: list[float] = []

    def optimize(self, request: ModelRequest) -> ModelResponse:
        self._check_rate_limit()
        started = perf_counter()
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                content = self._request_model(request)
                analysis = self.analyzer.analyze(content)
                analysis.optimized_prompt = content
                latency_ms = int((perf_counter() - started) * 1000)
                return ModelResponse(
                    analysis=analysis,
                    provider_used=self.name,
                    latency_ms=latency_ms,
                )
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    raise ProviderTimeoutError(f"{self.name} 请求超时。") from exc
                time.sleep(0.2 * (attempt + 1))
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    raise RuntimeError(f"{self.name} 请求失败。") from exc
                time.sleep(0.2 * (attempt + 1))
        raise RuntimeError(str(last_error) if last_error else f"{self.name} 请求失败。")

    def stream(self, request: ModelRequest) -> Iterator[str]:
        self._check_rate_limit()
        if not self.config.base_url or not self.config.api_key or not self.config.model:
            raise RuntimeError(f"{self.name} 缺少 base_url、api_key 或 model 配置。")
        with self.client.stream(
            "POST",
            self.config.base_url,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            json={
                "model": self.config.model,
                "stream": True,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一名提示词优化专家，请只返回优化后的完整提示词。",
                    },
                    {"role": "user", "content": self._build_prompt(request)},
                ],
            },
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                chunk = self._extract_stream_line(line)
                if chunk:
                    yield chunk

    def _check_rate_limit(self) -> None:
        now = time.monotonic()
        window_start = now - 60
        self._last_calls = [item for item in self._last_calls if item >= window_start]
        if len(self._last_calls) >= self.config.rate_limit_per_minute:
            raise ProviderRateLimitError(f"{self.name} 已达到每分钟限流。")
        self._last_calls.append(now)

    def _request_model(self, request: ModelRequest) -> str:
        if not self.config.base_url or not self.config.api_key or not self.config.model:
            raise RuntimeError(f"{self.name} 缺少 base_url、api_key 或 model 配置。")
        response = self.client.post(
            self.config.base_url,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            json={
                "model": self.config.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一名提示词优化专家，请只返回优化后的完整提示词。",
                    },
                    {"role": "user", "content": self._build_prompt(request)},
                ],
            },
        )
        response.raise_for_status()
        return self._extract_content(response.json())

    @staticmethod
    def _build_prompt(request: ModelRequest) -> str:
        if request.template is None:
            return request.prompt
        return f"可参考模板：\n{request.template.template}\n\n用户提示词：\n{request.prompt}"

    @staticmethod
    def _extract_content(payload: object) -> str:
        if not isinstance(payload, dict):
            raise RuntimeError("模型响应不是 JSON 对象。")
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
                text = first.get("text")
                if isinstance(text, str):
                    return text
        output = payload.get("output")
        if isinstance(output, str):
            return output
        raise RuntimeError(f"无法解析模型响应：{json.dumps(payload, ensure_ascii=False)[:200]}")

    @classmethod
    def _extract_stream_line(cls, line: str) -> str | None:
        clean_line = line.strip()
        if not clean_line:
            return None
        if clean_line.startswith("data: "):
            clean_line = clean_line.removeprefix("data: ").strip()
        if clean_line == "[DONE]":
            return None
        try:
            payload = json.loads(clean_line)
        except json.JSONDecodeError as exc:
            raise RuntimeError("无法解析流式模型响应。") from exc
        return cls._extract_stream_delta(payload)

    @staticmethod
    def _extract_stream_delta(payload: object) -> str | None:
        if not isinstance(payload, dict):
            return None
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                delta = first.get("delta")
                if isinstance(delta, dict):
                    content = delta.get("content")
                    if isinstance(content, str):
                        return content
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
        output = payload.get("output")
        if isinstance(output, str):
            return output
        return None
