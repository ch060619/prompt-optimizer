from __future__ import annotations

import os

import pytest

from prompt_optimizer.providers import (
    ModelRequest,
    ProviderConfig,
    ProviderConnectionTester,
    ProviderRegistry,
)

# RC ID: RC-173. Real Provider tests are manual-only and never default CI work.

CONFIRMATION = "I_UNDERSTAND_PROVIDER_FEES"


def test_real_provider_requires_explicit_manual_gate() -> None:
    if os.getenv("RABBIT_CODE_REAL_PROVIDER_TESTS") != "1":
        pytest.skip("real Provider tests are manual-only")

    provider_name = os.getenv("RABBIT_CODE_REAL_PROVIDER", "openai").strip()
    env_prefix = f"RABBIT_CODE_{provider_name.upper()}_API_KEY"
    if not os.getenv(env_prefix):
        raise RuntimeError(f"Set {env_prefix} with a credential you own before running this test.")
    if os.getenv("RABBIT_CODE_REAL_PROVIDER_CONFIRM") != CONFIRMATION:
        raise RuntimeError(
            f"Set RABBIT_CODE_REAL_PROVIDER_CONFIRM={CONFIRMATION} after reviewing "
            "possible charges."
        )
    try:
        token_limit = int(os.getenv("RABBIT_CODE_REAL_PROVIDER_MAX_TOKENS", "512"))
    except ValueError as exc:
        raise RuntimeError("RABBIT_CODE_REAL_PROVIDER_MAX_TOKENS must be an integer.") from exc

    provider = ProviderRegistry().get(provider_name)
    config = getattr(provider, "config", None)
    if not isinstance(config, ProviderConfig):
        raise RuntimeError(f"Provider {provider_name!r} has no configurable real adapter.")

    print(
        f"WARNING: this manual request may incur {provider_name} charges; "
        f"the configured token limit is {token_limit}."
    )

    def sender(_config: ProviderConfig, request: ModelRequest, _limit: int):
        yield from provider.stream(request)

    result = ProviderConnectionTester(real_sender=sender).run(
        config,
        mode="real",
        confirmed=True,
        token_limit=token_limit,
    )

    assert result.real_request_sent
    assert result.passed
