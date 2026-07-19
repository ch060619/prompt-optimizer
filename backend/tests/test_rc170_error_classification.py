from __future__ import annotations

import httpx
import pytest

from prompt_optimizer.providers import (
    AnthropicMessagesAdapter,
    AzureOpenAIAdapter,
    BedrockConverseAdapter,
    GeminiAdapter,
    ModelRequest,
    OpenAICompatibleAdapter,
    OpenAIResponsesAdapter,
    ProviderBalanceError,
    ProviderCancelledError,
    ProviderConfig,
    ProviderContentFilterError,
    ProviderErrorCategory,
    ProviderModelError,
    ProviderNetworkError,
    ProviderParameterError,
    ProviderRateLimitError,
    ProviderRegionError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderUnauthorizedError,
    VertexAIAdapter,
)
from prompt_optimizer.public import provider_error_presentation


def _config() -> ProviderConfig:
    return ProviderConfig(
        name="openai",
        base_url="https://provider.test/v1",
        api_key="owned-key",
        model="model-a",
        max_retries=0,
    )


ERROR_FIXTURES = [
    (
        401,
        {"error": {"code": "invalid_api_key", "message": "bad key"}},
        ProviderUnauthorizedError,
        "auth",
    ),
    (
        402,
        {"error": {"code": "insufficient_quota", "message": "billing required"}},
        ProviderBalanceError,
        "balance",
    ),
    (
        429,
        {"error": {"code": "rate_limit_exceeded", "message": "slow down"}},
        ProviderRateLimitError,
        "rate_limit",
    ),
    (
        403,
        {"error": {"code": "unsupported_region", "message": "region blocked"}},
        ProviderRegionError,
        "region",
    ),
    (
        404,
        {"error": {"code": "model_not_found", "message": "unknown model"}},
        ProviderModelError,
        "model",
    ),
    (
        400,
        {"error": {"code": "invalid_request_error", "message": "bad parameter"}},
        ProviderParameterError,
        "parameter",
    ),
    (
        400,
        {"error": {"code": "content_filter", "message": "safety policy"}},
        ProviderContentFilterError,
        "filter",
    ),
    (
        408,
        {"error": {"code": "request_timeout", "message": "timed out"}},
        ProviderTimeoutError,
        "timeout",
    ),
    (
        500,
        {"error": {"code": "internal_error", "message": "provider failed"}},
        ProviderServerError,
        "server",
    ),
]


@pytest.mark.parametrize("status,payload,error_type,category", ERROR_FIXTURES)
def test_openai_error_fixtures_map_to_canonical_categories(
    status: int,
    payload: dict[str, object],
    error_type: type[Exception],
    category: str,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status,
            json=payload,
            headers={"x-request-id": "req-rc170-001"},
            request=request,
        )

    provider = OpenAICompatibleAdapter(
        _config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(error_type) as raised:
        provider.optimize(ModelRequest(prompt="分类夹具"))

    assert raised.value.category == ProviderErrorCategory(category)
    assert raised.value.request_id == "req-rc170-001"


@pytest.mark.parametrize(
    "adapter_type",
    [
        OpenAICompatibleAdapter,
        OpenAIResponsesAdapter,
        GeminiAdapter,
        AnthropicMessagesAdapter,
        AzureOpenAIAdapter,
        VertexAIAdapter,
        BedrockConverseAdapter,
    ],
)
def test_all_provider_adapters_share_http_error_mapping(adapter_type: type[object]) -> None:
    response = httpx.Response(
        403,
        json={"error": {"code": "unsupported_region", "message": "region blocked"}},
        headers={"request-id": "req-rc170-region"},
        request=httpx.Request("POST", "https://provider.test/v1/chat/completions"),
    )

    with pytest.raises(ProviderRegionError) as raised:
        adapter_type._raise_for_status(response)  # type: ignore[attr-defined]

    assert raised.value.category == ProviderErrorCategory.REGION
    assert raised.value.request_id == "req-rc170-region"


def test_network_timeout_and_cancelled_errors_have_shared_presentation() -> None:
    network = ProviderNetworkError("network unavailable")
    timeout = ProviderTimeoutError("timed out")
    cancelled = ProviderCancelledError("cancelled")

    network_view = provider_error_presentation(network)
    timeout_view = provider_error_presentation(timeout)

    assert (network_view.category, network_view.code, network_view.recovery_action) == (
        "network",
        "PROVIDER_NETWORK",
        "check_network",
    )
    assert (timeout_view.category, timeout_view.code, timeout_view.recovery_action) == (
        "timeout",
        "PROVIDER_TIMEOUT",
        "retry",
    )
    assert network_view.exit_code != timeout_view.exit_code
    cancelled_view = provider_error_presentation(cancelled)
    assert (cancelled_view.category, cancelled_view.code, cancelled_view.recovery_action) == (
        "cancelled",
        "REQUEST_CANCELLED",
        "cancel",
    )


def test_invalid_request_id_is_not_exposed() -> None:
    error = ProviderServerError("server failed", request_id="api-key=secret")

    assert error.request_id is None
    assert provider_error_presentation(error).request_id is None
