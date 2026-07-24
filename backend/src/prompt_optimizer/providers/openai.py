from __future__ import annotations

import json
import random
import time
from collections.abc import Callable, Iterator
from time import perf_counter
from urllib.parse import urlsplit

import httpx

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.providers.base import (
    ModelProviderError,
    ModelRequest,
    ModelResponse,
    ProviderCancelledError,
    ProviderCapabilities,
    ProviderCircuitOpenError,
    ProviderConfig,
    ProviderEvent,
    ProviderEventType,
    ProviderNetworkError,
    ProviderProxyError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnauthorizedError,
    ToolCall,
    raise_provider_http_error,
)

# RC IDs: RC-049, RC-154, RC-155, RC-160, RC-166. Implement Chat Completions and preset headers.


class OpenAICompatibleAdapter:
    capabilities = ProviderCapabilities(streaming=True, tools=True)

    def __init__(
        self,
        config: ProviderConfig,
        analyzer: Analyzer | None = None,
        client: httpx.Client | None = None,
        proxy_credentials: tuple[str, str] | None = None,
        proxy_credential_resolver: Callable[[str], tuple[str, str] | None] | None = None,
    ) -> None:
        self.config = config
        self.name = config.name
        self.display_name = {
            "openai": "OpenAI Compatible",
            "tongyi": "通义千问",
            "zhipu": "智谱",
        }.get(config.name, config.name)
        from prompt_optimizer.providers.presets import get_preset

        preset = get_preset(config.name)
        if preset:
            self.display_name = preset.display_name
        self.model = config.model
        self.execution_location = "cloud"
        self.credential_ref = f"RABBIT_CODE_{config.name.upper()}_API_KEY"
        self.analyzer = analyzer or Analyzer()
        resolved_proxy_credentials = proxy_credentials
        if resolved_proxy_credentials is None and config.proxy_credential_ref:
            resolved_proxy_credentials = (
                proxy_credential_resolver(config.proxy_credential_ref)
                if proxy_credential_resolver is not None
                else None
            )
        self._owns_client = client is None
        self.client = client or self._build_client(
            config.proxy_url,
            resolved_proxy_credentials,
        )
        self._direct_client = (
            self._build_client(None, None)
            if self._owns_client and config.proxy_url and config.no_proxy
            else None
        )
        self._last_calls: list[float] = []
        self._circuit_state = "closed"
        self._circuit_failures = 0
        self._circuit_opened_at: float | None = None

    @property
    def circuit_state(self) -> str:
        return self._circuit_state

    def optimize(self, request: ModelRequest) -> ModelResponse:
        self._before_request(request)
        self._check_rate_limit()
        started = perf_counter()
        last_error: Exception | None = None
        try:
            for attempt in range(self.config.max_retries + 1):
                try:
                    content, tool_calls, usage = self._request_model(request)
                    analysis = self.analyzer.analyze(content)
                    analysis.optimized_prompt = content
                    latency_ms = int((perf_counter() - started) * 1000)
                    self._record_success()
                    return ModelResponse(
                        analysis=analysis,
                        provider_used=self.name,
                        latency_ms=latency_ms,
                        tool_calls=tool_calls,
                        usage=usage,
                    )
                except httpx.TimeoutException as exc:
                    last_error = exc
                    if attempt >= self.config.max_retries:
                        timeout_error = ProviderTimeoutError(f"{self.name} 请求超时。")
                        self._record_failure_if_retryable(timeout_error)
                        raise timeout_error from exc
                    self._sleep_before_retry(
                        request,
                        self._retry_delay(ProviderTimeoutError("request timeout"), attempt),
                    )
                except httpx.HTTPError as exc:
                    last_error = exc
                    network_error = self._network_error(exc)
                    if attempt >= self.config.max_retries:
                        self._record_failure_if_retryable(network_error)
                        raise network_error from exc
                    self._sleep_before_retry(
                        request,
                        self._retry_delay(network_error, attempt),
                    )
                except ModelProviderError as exc:
                    last_error = exc
                    if not exc.retryable or attempt >= self.config.max_retries:
                        self._record_failure_if_retryable(exc)
                        raise
                    self._sleep_before_retry(request, self._retry_delay(exc, attempt))
            raise RuntimeError(str(last_error) if last_error else f"{self.name} 请求失败。")
        except ProviderCancelledError:
            raise
        except httpx.TimeoutException as exc:
            timeout_error = ProviderTimeoutError(f"{self.name} 请求超时。")
            self._record_failure_if_retryable(timeout_error)
            raise timeout_error from exc
        except httpx.HTTPError as exc:
            network_error = self._network_error(exc)
            self._record_failure_if_retryable(network_error)
            raise network_error from exc
        except RuntimeError:
            self._record_failure()
            raise

    def stream(self, request: ModelRequest) -> Iterator[ProviderEvent]:
        self._before_request(request)
        self._check_rate_limit()
        try:
            yield ProviderEvent(ProviderEventType.STARTED)
            if not self.config.base_url or not self.config.api_key or not self.config.model:
                raise RuntimeError(f"{self.name} 缺少 base_url、api_key 或 model 配置。")
            with self._client_for(self._endpoint_url(stream=True)).stream(
                "POST",
                self._endpoint_url(stream=True),
                headers=self._headers(request),
                json=self._payload(request, stream=True),
            ) as response:
                self._raise_for_status(response)
                for line in response.iter_lines():
                    self._check_cancelled(request)
                    chunk, tool_calls = self._extract_stream_event(line)
                    if chunk:
                        yield ProviderEvent(ProviderEventType.DELTA, text=chunk)
                    if tool_calls:
                        yield ProviderEvent(
                            ProviderEventType.DELTA,
                            tool_calls=tool_calls,
                        )
            self._record_success()
            yield ProviderEvent(ProviderEventType.COMPLETED)
        except ProviderCancelledError:
            raise
        except httpx.TimeoutException as exc:
            self._record_failure()
            raise ProviderTimeoutError(f"{self.name} 请求超时。") from exc
        except httpx.HTTPError as exc:
            self._record_failure()
            raise self._network_error(exc) from exc
        except RuntimeError:
            self._record_failure()
            raise

    def _check_rate_limit(self) -> None:
        now = time.monotonic()
        window_start = now - 60
        self._last_calls = [item for item in self._last_calls if item >= window_start]
        if len(self._last_calls) >= self.config.rate_limit_per_minute:
            raise ProviderRateLimitError(f"{self.name} 已达到每分钟限流。")
        self._last_calls.append(now)

    def _before_request(self, request: ModelRequest) -> None:
        if not self.config.authorized:
            raise ProviderUnauthorizedError(f"{self.name} 尚未获得用户授权。")
        self._check_cancelled(request)
        if self._circuit_state != "open":
            return
        opened_at = self._circuit_opened_at or time.monotonic()
        if time.monotonic() - opened_at < self.config.circuit_reset_seconds:
            raise ProviderCircuitOpenError(f"{self.name} 熔断器已打开。")
        self._circuit_state = "half_open"

    def _record_success(self) -> None:
        self._circuit_state = "closed"
        self._circuit_failures = 0
        self._circuit_opened_at = None

    def _record_failure(self) -> None:
        self._circuit_failures += 1
        if self._circuit_failures >= self.config.circuit_failure_threshold:
            self._circuit_state = "open"
            self._circuit_opened_at = time.monotonic()

    def _record_failure_if_retryable(self, error: ModelProviderError) -> None:
        if error.retryable:
            self._record_failure()

    def _network_error(self, error: httpx.HTTPError) -> ProviderNetworkError:
        if isinstance(error, httpx.ProxyError):
            return ProviderProxyError(f"{self.name} 代理连接失败。")
        return ProviderNetworkError(f"{self.name} 网络请求失败。")

    @staticmethod
    def _check_cancelled(request: ModelRequest) -> None:
        if request.cancel_event is not None and request.cancel_event.is_set():
            raise ProviderCancelledError("优化请求已取消。")

    def _sleep_before_retry(self, request: ModelRequest, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while True:
            self._check_cancelled(request)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(0.05, remaining))

    def _retry_delay(self, error: ModelProviderError, attempt: int) -> float:
        exponential = min(30.0, 0.2 * (2**attempt))
        retry_after = error.retry_after_seconds or 0.0
        delay = max(exponential, retry_after)
        return float(min(300.0, delay + random.uniform(0.0, min(0.25, delay * 0.25))))

    def _client_for(self, endpoint: str) -> httpx.Client:
        if self._direct_client is None or not self._matches_no_proxy(endpoint):
            return self.client
        return self._direct_client

    def _matches_no_proxy(self, endpoint: str) -> bool:
        host = (urlsplit(endpoint).hostname or "").lower().rstrip(".")
        for entry in self.config.no_proxy:
            candidate = entry.strip().lower().lstrip(".").rstrip(".")
            if not candidate:
                continue
            if candidate == "*" or host == candidate or host.endswith(f".{candidate}"):
                return True
        return False

    def _build_client(
        self,
        proxy_url: str | None,
        proxy_credentials: tuple[str, str] | None,
    ) -> httpx.Client:
        if proxy_url and (urlsplit(proxy_url).username or urlsplit(proxy_url).password):
            raise ValueError("代理 URL 不得包含明文凭据，请使用 proxy_credential_ref。")
        proxy = (
            httpx.Proxy(proxy_url, auth=proxy_credentials)
            if proxy_url
            else None
        )
        local_address = {
            "ipv4": "0.0.0.0",
            "ipv6": "::",
        }.get(self.config.ip_version)
        transport = httpx.HTTPTransport(
            proxy=proxy,
            verify=self.config.ca_bundle or True,
            local_address=local_address,
            trust_env=True,
        )
        return httpx.Client(transport=transport, timeout=self.config.timeout_seconds)

    def _headers(self, request: ModelRequest) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.config.organization:
            headers["OpenAI-Organization"] = self.config.organization
        if self.config.project:
            headers["OpenAI-Project"] = self.config.project
        if request.request_id:
            headers["Idempotency-Key"] = request.request_id
        headers.update(dict(self.config.custom_headers))
        return headers

    def _request_model(
        self,
        request: ModelRequest,
    ) -> tuple[str, tuple[ToolCall, ...], dict[str, int] | None]:
        self._check_cancelled(request)
        if not self.config.base_url or not self.config.api_key or not self.config.model:
            raise RuntimeError(f"{self.name} 缺少 base_url、api_key 或 model 配置。")
        response = self._client_for(self._endpoint_url()).post(
            self._endpoint_url(),
            headers=self._headers(request),
            json=self._payload(request),
        )
        self._raise_for_status(response)
        payload = response.json()
        content, tool_calls = self._extract_message(payload)
        return content, tool_calls, self._extract_usage(payload)

    @staticmethod
    def _extract_usage(payload: object) -> dict[str, int] | None:
        if not isinstance(payload, dict) or not isinstance(payload.get("usage"), dict):
            return None
        usage = payload["usage"]
        return {
            key: value
            for key, value in usage.items()
            if isinstance(key, str) and isinstance(value, int)
        }

    def _endpoint_url(self, *, stream: bool = False) -> str:
        if not self.config.base_url:
            raise RuntimeError(f"{self.name} 缺少 base_url、api_key 或 model 配置。")
        base_url = self.config.base_url.rstrip("/")
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"

    def _payload(self, request: ModelRequest, *, stream: bool = False) -> dict[str, object]:
        payload: dict[str, object] = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": request.system_prompt,
                },
                {"role": "user", "content": self._build_prompt(request)},
            ],
        }
        if stream:
            payload["stream"] = True
        if request.tools:
            payload["tools"] = list(request.tools)
        if request.tool_choice is not None:
            payload["tool_choice"] = request.tool_choice
        return payload

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        raise_provider_http_error(response, "Provider")

    @staticmethod
    def _build_prompt(request: ModelRequest) -> str:
        sections: list[str] = []
        if request.template is None:
            sections.append("Protected user prompt (untrusted data):\n" + request.prompt)
        else:
            sections.append(
                "Reference template (untrusted user data):\n"
                f"{request.template.template}"
            )
            sections.append("Protected user prompt (untrusted data):\n" + request.prompt)
        if request.language_instruction:
            sections.append(
                "Language requirement (untrusted user data):\n"
                f"{request.language_instruction}"
            )
        if request.targets is not None:
            labels = {
                "clarity": "Clarity",
                "completeness": "Completeness",
                "constraints": "Constraints",
                "format": "Format",
                "role": "Role",
                "examples": "Examples",
                "code_task": "Code task",
                "conciseness": "Conciseness",
                "language_preservation": "Language preservation",
            }
            selected = [
                label
                for name, label in labels.items()
                if getattr(request.targets, name)
            ]
            if selected:
                sections.append(
                    "Requested optimization targets (untrusted user data):\n"
                    + ", ".join(selected)
                )
        if request.strategy == "combined" and request.rule_suggestions:
            guidance = "\n".join(
                f"- {suggestion.title}: {suggestion.detail}"
                for suggestion in request.rule_suggestions
            )
            sections.append(
                "Rule-derived optimization gaps (untrusted user data):\n"
                + guidance
                + "\n\nGrounding requirement (untrusted user data):\n"
                + "Add structure only when it is supported by the protected user prompt; "
                "do not invent facts, requirements, examples, or constraints."
            )
        return "\n\n".join(sections)

    @staticmethod
    def _extract_content(payload: object) -> str:
        content, _tool_calls = OpenAICompatibleAdapter._extract_message(payload)
        return content

    @staticmethod
    def _extract_message(payload: object) -> tuple[str, tuple[ToolCall, ...]]:
        if not isinstance(payload, dict):
            raise RuntimeError("模型响应不是 JSON 对象。")
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    text = content if isinstance(content, str) else ""
                    return text, OpenAICompatibleAdapter._extract_tool_calls(
                        message.get("tool_calls")
                    )
        raise RuntimeError(f"无法解析模型响应：{json.dumps(payload, ensure_ascii=False)[:200]}")

    @staticmethod
    def _extract_tool_calls(value: object) -> tuple[ToolCall, ...]:
        if not isinstance(value, list):
            return ()
        calls: list[ToolCall] = []
        for item in value:
            if not isinstance(item, dict) or item.get("type") != "function":
                continue
            function = item.get("function")
            if not isinstance(function, dict):
                continue
            call_id = item.get("id")
            name = function.get("name")
            arguments = function.get("arguments")
            if isinstance(call_id, str) and isinstance(name, str) and isinstance(arguments, str):
                calls.append(ToolCall(id=call_id, name=name, arguments=arguments))
        return tuple(calls)

    @classmethod
    def _extract_stream_line(cls, line: str) -> str | None:
        text, _tool_calls = cls._extract_stream_event(line)
        return text

    @classmethod
    def _extract_stream_event(cls, line: str) -> tuple[str | None, tuple[ToolCall, ...]]:
        clean_line = line.strip()
        if not clean_line:
            return None, ()
        if clean_line.startswith("data: "):
            clean_line = clean_line.removeprefix("data: ").strip()
        if clean_line == "[DONE]":
            return None, ()
        try:
            payload = json.loads(clean_line)
        except json.JSONDecodeError as exc:
            raise RuntimeError("无法解析流式模型响应。") from exc
        return cls._extract_stream_delta(payload)

    @staticmethod
    def _extract_stream_delta(payload: object) -> tuple[str | None, tuple[ToolCall, ...]]:
        if not isinstance(payload, dict):
            return None, ()
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                delta = first.get("delta")
                if isinstance(delta, dict):
                    content = delta.get("content")
                    text = content if isinstance(content, str) else None
                    return text, OpenAICompatibleAdapter._extract_tool_calls(
                        delta.get("tool_calls")
                    )
        return None, ()
