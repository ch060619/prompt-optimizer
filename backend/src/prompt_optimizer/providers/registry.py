from __future__ import annotations

from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.identity import compatible_env
from prompt_optimizer.providers.base import ModelProvider, ProviderConfig
from prompt_optimizer.providers.offline import OfflineRuleProvider
from prompt_optimizer.providers.openai import OpenAICompatibleAdapter

# RC ID: RC-054. Prefer Rabbit Code Provider environment names with a legacy fallback.
# RC ID: RC-049. Register the explicit OpenAI-compatible adapter for compatible endpoints.


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
        provider = OpenAICompatibleAdapter(config)
        self._providers[name] = provider
        return provider

    @staticmethod
    def _config_from_env(name: str) -> ProviderConfig:
        return ProviderConfig(
            name=name,
            base_url=compatible_env(f"{name.upper()}_BASE_URL"),
            api_key=compatible_env(f"{name.upper()}_API_KEY"),
            model=compatible_env(f"{name.upper()}_MODEL"),
            timeout_seconds=float(compatible_env(f"{name.upper()}_TIMEOUT_SECONDS") or "20"),
            max_retries=int(compatible_env(f"{name.upper()}_MAX_RETRIES") or "2"),
            rate_limit_per_minute=int(
                compatible_env(f"{name.upper()}_RATE_LIMIT_PER_MINUTE") or "30"
            ),
        )
