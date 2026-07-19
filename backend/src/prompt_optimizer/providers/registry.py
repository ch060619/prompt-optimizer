from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Literal, cast

from prompt_optimizer.contracts import PromptOptimizer, Provider
from prompt_optimizer.core.models import ProviderHealth, ProviderSelectionScope
from prompt_optimizer.identity import compatible_env
from prompt_optimizer.providers.anthropic import AnthropicMessagesAdapter
from prompt_optimizer.providers.base import ProviderConfig
from prompt_optimizer.providers.discovery import ModelDiscoveryResult, ModelDiscoveryService
from prompt_optimizer.providers.gemini import GeminiAdapter
from prompt_optimizer.providers.hosted import (
    AzureOpenAIAdapter,
    BedrockConverseAdapter,
    VertexAIAdapter,
)
from prompt_optimizer.providers.local import LocalModelProvider, LocalModelRunner
from prompt_optimizer.providers.offline import OfflineRuleProvider
from prompt_optimizer.providers.openai import OpenAICompatibleAdapter
from prompt_optimizer.providers.presets import get_preset
from prompt_optimizer.providers.responses import OpenAIResponsesAdapter
from prompt_optimizer.providers.selection import ModelSelectionStore

# RC ID: RC-054. Prefer Rabbit Code Provider environment names with a legacy fallback.
# RC IDs: RC-049, RC-161, RC-162, RC-163, RC-165, RC-166, RC-168. Register adapters and discovery.


@dataclass(frozen=True)
class ProviderSelection:
    name: str
    model: str | None
    scope: ProviderSelectionScope
    health: ProviderHealth
    provider: Provider
    fallback_chain: tuple[str, ...] = ()


class ProviderRegistry:
    def __init__(
        self,
        optimizer: PromptOptimizer | None = None,
        providers: dict[str, Provider] | None = None,
        local_runner: LocalModelRunner | None = None,
        model_discovery: ModelDiscoveryService | None = None,
        selection_store: ModelSelectionStore | None = None,
    ) -> None:
        self._providers: dict[str, Provider] = providers or {
            "offline": OfflineRuleProvider(optimizer),
            "local": LocalModelProvider(local_runner),
        }
        self._model_discovery = model_discovery or ModelDiscoveryService()
        self.selection_store = selection_store or ModelSelectionStore()

    def discover_models(
        self,
        name: str,
        *,
        stored_models: tuple[str, ...] = (),
        manual_model: str | None = None,
        force: bool = False,
    ) -> ModelDiscoveryResult:
        existing = self._providers.get(name)
        configured = getattr(existing, "config", None)
        config = (
            configured
            if isinstance(configured, ProviderConfig)
            else self._config_from_env(name)
        )
        return self._model_discovery.discover(
            config,
            stored_models=stored_models,
            manual_model=manual_model,
            force=force,
        )

    def get(self, name: str, model_override: str | None = None) -> Provider:
        if name in self._providers:
            existing = self._providers[name]
            if model_override and hasattr(existing, "config"):
                config = replace(existing.config, model=model_override)  # type: ignore[attr-defined]
                return self._http_adapter(config)
            return self._providers[name]
        if name == "local":
            provider: Provider = LocalModelProvider()
            self._providers[name] = provider
            return provider
        config = self._config_from_env(name)
        if model_override:
            config = replace(config, model=model_override)
        provider = self._http_adapter(config)
        self._providers[name] = provider
        return provider

    @staticmethod
    def _http_adapter(config: ProviderConfig) -> Provider:
        if config.api_protocol == "responses":
            return OpenAIResponsesAdapter(config)
        if config.api_protocol == "gemini" or config.name == "gemini":
            return GeminiAdapter(config)
        if config.api_protocol == "anthropic" or config.name == "anthropic":
            return AnthropicMessagesAdapter(config)
        if config.api_protocol == "azure_openai" or config.name in {"azure", "azure_openai"}:
            return AzureOpenAIAdapter(config)
        if config.api_protocol == "vertex" or config.name == "vertex":
            return VertexAIAdapter(config)
        if config.api_protocol == "bedrock" or config.name == "bedrock":
            return BedrockConverseAdapter(config)
        return OpenAICompatibleAdapter(config)

    def resolve(
        self,
        *,
        session_provider: str | None,
        session_model: str | None,
        optimizer_provider: str | None,
        optimizer_model: str | None,
    ) -> ProviderSelection:
        session_route, session_scope = self.selection_store.resolve_session(
            provider=session_provider,
            model=session_model,
        )
        session_name = session_route.provider
        session = self.get(session_name, session_route.model)
        session_selection = ProviderSelection(
            name=session_name,
            model=session_route.model or getattr(session, "model", None),
            scope=session_scope,
            health=(
                "healthy"
                if self.is_available(session, session_route.model)
                else "unavailable"
            ),
            provider=session,
            fallback_chain=("offline",) if session_name != "offline" else (),
        )
        optimizer_route = self.selection_store.resolve_optimizer(
            provider=optimizer_provider,
            model=optimizer_model,
            session=session_route,
        )
        if optimizer_route is None:
            return session_selection

        optimizer_name = optimizer_route.provider
        optimizer = self.get(optimizer_name, optimizer_route.model)
        fallback_chain = tuple(
            dict.fromkeys(
                name
                for name in (optimizer_name, session_name, "offline")
                if name != optimizer_name or name == "offline"
            )
        )
        optimizer_selection = ProviderSelection(
            name=optimizer_name,
            model=optimizer_route.model or getattr(optimizer, "model", None),
            scope="optimizer",
            health=(
                "healthy"
                if self.is_available(optimizer, optimizer_route.model)
                else "unavailable"
            ),
            provider=optimizer,
            fallback_chain=fallback_chain,
        )
        if optimizer_selection.health == "healthy":
            return optimizer_selection
        if session_selection.health == "healthy":
            return ProviderSelection(
                name=session_selection.name,
                model=session_selection.model,
                scope=session_selection.scope,
                health="fallback",
                provider=session_selection.provider,
                fallback_chain=fallback_chain,
            )
        return optimizer_selection

    @staticmethod
    def is_available(provider: Provider, model_override: str | None = None) -> bool:
        if getattr(provider, "name", None) == "offline":
            return True
        health = getattr(provider, "health", None)
        if callable(health):
            return bool(health().ready)
        configured = getattr(provider, "config", None)
        if configured is None:
            return True
        return bool(
            configured.base_url
            and configured.api_key
            and (model_override or configured.model)
            and configured.authorized
        )

    @staticmethod
    def _config_from_env(name: str) -> ProviderConfig:
        raw_protocol = compatible_env(f"{name.upper()}_API_PROTOCOL")
        supported_protocols = {
            "chat_completions",
            "responses",
            "gemini",
            "anthropic",
            "azure_openai",
            "vertex",
            "bedrock",
        }
        default_protocol = {
            "gemini": "gemini",
            "anthropic": "anthropic",
            "azure": "azure_openai",
            "azure_openai": "azure_openai",
            "vertex": "vertex",
            "bedrock": "bedrock",
        }.get(name, "chat_completions")
        api_protocol = cast(
            Literal[
                "chat_completions",
                "responses",
                "gemini",
                "anthropic",
                "azure_openai",
                "vertex",
                "bedrock",
            ],
            raw_protocol if raw_protocol in supported_protocols else default_protocol,
        )
        raw_beta_features = compatible_env(f"{name.upper()}_BETA_FEATURES") or ""
        raw_no_proxy = compatible_env(f"{name.upper()}_NO_PROXY") or ""
        raw_ip_version = compatible_env(f"{name.upper()}_IP_VERSION") or "any"
        preset = get_preset(name)
        raw_headers = compatible_env(f"{name.upper()}_HEADERS_JSON") or "{}"
        try:
            header_payload = json.loads(raw_headers)
        except json.JSONDecodeError:
            header_payload = {}
        custom_headers = (
            tuple((str(key), str(value)) for key, value in header_payload.items())
            if isinstance(header_payload, dict)
            else ()
        )
        default_base_url = preset.base_url if preset else None
        return ProviderConfig(
            name=name,
            base_url=compatible_env(f"{name.upper()}_BASE_URL") or default_base_url,
            api_key=compatible_env(f"{name.upper()}_API_KEY"),
            model=compatible_env(f"{name.upper()}_MODEL"),
            organization=compatible_env(f"{name.upper()}_ORGANIZATION"),
            project=compatible_env(f"{name.upper()}_PROJECT"),
            project_id=compatible_env(f"{name.upper()}_PROJECT_ID"),
            region=compatible_env(f"{name.upper()}_REGION"),
            deployment=compatible_env(f"{name.upper()}_DEPLOYMENT"),
            api_protocol=api_protocol,
            api_version=compatible_env(f"{name.upper()}_API_VERSION"),
            beta_features=tuple(
                value.strip() for value in raw_beta_features.split(",") if value.strip()
            ),
            prompt_caching=(
                (compatible_env(f"{name.upper()}_PROMPT_CACHING") or "").lower()
                in {"1", "true", "yes", "on"}
            ),
            credential_mode=cast(
                Literal["api_key", "bearer", "aws_sigv4"],
                compatible_env(f"{name.upper()}_CREDENTIAL_MODE") or "api_key",
            ),
            custom_headers=custom_headers,
            proxy_url=compatible_env(f"{name.upper()}_PROXY_URL"),
            no_proxy=tuple(
                value.strip()
                for value in raw_no_proxy.split(",")
                if value.strip()
            ),
            ca_bundle=compatible_env(f"{name.upper()}_CA_BUNDLE"),
            ip_version=cast(
                Literal["any", "ipv4", "ipv6"],
                raw_ip_version if raw_ip_version in {"any", "ipv4", "ipv6"} else "any",
            ),
            proxy_credential_ref=compatible_env(
                f"{name.upper()}_PROXY_CREDENTIAL_REF"
            ),
            input_cost_per_1k_tokens=float(
                compatible_env(f"{name.upper()}_INPUT_COST_PER_1K") or "0"
            ),
            output_cost_per_1k_tokens=float(
                compatible_env(f"{name.upper()}_OUTPUT_COST_PER_1K") or "0"
            ),
            output_token_reserve=int(
                compatible_env(f"{name.upper()}_OUTPUT_TOKEN_RESERVE") or "256"
            ),
            timeout_seconds=float(compatible_env(f"{name.upper()}_TIMEOUT_SECONDS") or "20"),
            max_retries=int(compatible_env(f"{name.upper()}_MAX_RETRIES") or "2"),
            rate_limit_per_minute=int(
                compatible_env(f"{name.upper()}_RATE_LIMIT_PER_MINUTE") or "30"
            ),
            authorized=(
                compatible_env(f"{name.upper()}_AUTHORIZED") or ""
            ).lower()
            in {"1", "true", "yes", "on"},
        )
