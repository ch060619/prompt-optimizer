from __future__ import annotations

import os

from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.providers.base import ModelProvider, ProviderConfig
from prompt_optimizer.providers.http import HttpChatProvider
from prompt_optimizer.providers.offline import OfflineRuleProvider


class ProviderRegistry:
    def __init__(
        self,
        optimizer: Optimizer | None = None,
        providers: dict[str, ModelProvider] | None = None,
    ) -> None:
        self._providers: dict[str, ModelProvider] = providers or {
            "offline": OfflineRuleProvider(optimizer),
        }

    def get(self, name: str) -> ModelProvider:
        if name in self._providers:
            return self._providers[name]
        config = self._config_from_env(name)
        provider = HttpChatProvider(config)
        self._providers[name] = provider
        return provider

    def close(self) -> None:
        for provider in self._providers.values():
            client = getattr(provider, "client", None)
            if client is not None:
                client.close()

    @staticmethod
    def _config_from_env(name: str) -> ProviderConfig:
        prefix = f"PROMPT_OPTIMIZER_{name.upper()}"
        return ProviderConfig(
            name=name,
            base_url=os.getenv(f"{prefix}_BASE_URL"),
            api_key=os.getenv(f"{prefix}_API_KEY"),
            model=os.getenv(f"{prefix}_MODEL"),
            timeout_seconds=float(os.getenv(f"{prefix}_TIMEOUT_SECONDS", "20")),
            max_retries=int(os.getenv(f"{prefix}_MAX_RETRIES", "2")),
            rate_limit_per_minute=int(os.getenv(f"{prefix}_RATE_LIMIT_PER_MINUTE", "30")),
        )
