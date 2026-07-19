from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, replace
from time import monotonic
from typing import Any, Literal, cast

from prompt_optimizer.providers.base import ProviderCapabilities

# RC ID: RC-167. Version and cache Provider capability declarations and probes.

CAPABILITY_SCHEMA_VERSION = "v1"
CapabilitySource = Literal["static", "probe"]
CapabilityProbe = Callable[[], object]

_PROBE_ALIASES = {
    "images": "image",
    "vision": "image",
    "tool_use": "tools",
}
_CAPABILITY_FIELDS = {item.name for item in fields(ProviderCapabilities)}


@dataclass(frozen=True)
class CapabilitySnapshot:
    provider: str
    model: str | None
    capabilities: ProviderCapabilities
    schema_version: str
    source: CapabilitySource
    observed_at: float
    expires_at: float
    probe_error: str | None = None

    def is_expired(self, now: float) -> bool:
        return now >= self.expires_at or self.schema_version != CAPABILITY_SCHEMA_VERSION

    def supports(self, capability: str) -> bool:
        value = getattr(self.capabilities, capability, False)
        return bool(value)

    def as_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "schema_version": self.schema_version,
            "source": self.source,
            "observed_at": self.observed_at,
            "expires_at": self.expires_at,
            "capabilities": {
                item.name: getattr(self.capabilities, item.name)
                for item in fields(self.capabilities)
            },
            "probe_error": self.probe_error,
        }


class ProviderCapabilityResolver:
    """Resolve static adapter capabilities with short-lived probe overrides."""

    def __init__(
        self,
        *,
        ttl_seconds: float = 300.0,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero")
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._cache: dict[tuple[str, str | None], CapabilitySnapshot] = {}

    def resolve(
        self,
        provider: object,
        *,
        probe: CapabilityProbe | None = None,
        force: bool = False,
    ) -> CapabilitySnapshot:
        provider_name = str(getattr(provider, "name", type(provider).__name__))
        raw_model = getattr(provider, "model", None)
        model = raw_model if isinstance(raw_model, str) else None
        key = (provider_name, model)
        now = self._clock()
        cached = self._cache.get(key)
        if cached is not None and not force and not cached.is_expired(now):
            return cached

        declared = getattr(provider, "capabilities", ProviderCapabilities())
        if not isinstance(declared, ProviderCapabilities):
            raise TypeError(f"{provider_name} has an invalid capability declaration")
        probe_fn = probe or self._provider_probe(provider)
        capabilities = declared
        source: CapabilitySource = "static"
        probe_error: str | None = None
        if probe_fn is not None:
            try:
                capabilities = _merge_probe_result(declared, probe_fn())
                source = "probe" if capabilities != declared else "static"
            except Exception as exc:  # Probe failures must not hide a valid static contract.
                probe_error = type(exc).__name__

        snapshot = CapabilitySnapshot(
            provider=provider_name,
            model=model,
            capabilities=capabilities,
            schema_version=CAPABILITY_SCHEMA_VERSION,
            source=source,
            observed_at=now,
            expires_at=now + self.ttl_seconds,
            probe_error=probe_error,
        )
        self._cache[key] = snapshot
        return snapshot

    def clear(self, provider: object | None = None) -> None:
        if provider is None:
            self._cache.clear()
            return
        provider_name = str(getattr(provider, "name", type(provider).__name__))
        raw_model = getattr(provider, "model", None)
        model = raw_model if isinstance(raw_model, str) else None
        self._cache.pop((provider_name, model), None)

    @staticmethod
    def _provider_probe(provider: object) -> CapabilityProbe | None:
        candidate = getattr(provider, "probe_capabilities", None)
        return candidate if callable(candidate) else None


def _merge_probe_result(
    declared: ProviderCapabilities,
    result: object,
) -> ProviderCapabilities:
    if isinstance(result, ProviderCapabilities):
        return result
    if not isinstance(result, Mapping):
        raise TypeError("capability probe must return a mapping or ProviderCapabilities")
    overrides: dict[str, bool | int | None] = {}
    for raw_name, value in result.items():
        if not isinstance(raw_name, str):
            continue
        name = _PROBE_ALIASES.get(raw_name, raw_name)
        if name not in _CAPABILITY_FIELDS:
            continue
        if name == "context_length":
            if value is None or (isinstance(value, int) and not isinstance(value, bool)):
                overrides[name] = value
            continue
        if isinstance(value, bool):
            overrides[name] = value
    return (
        cast(ProviderCapabilities, replace(cast(Any, declared), **overrides))
        if overrides
        else declared
    )


# The matrix is intentionally explicit so a changed adapter declaration is caught by contract tests.
CAPABILITY_MATRIX: Mapping[str, ProviderCapabilities] = {
    "chat_completions": ProviderCapabilities(streaming=True, tools=True),
    "responses": ProviderCapabilities(streaming=True, tools=True, structured_output=True),
    "gemini": ProviderCapabilities(streaming=True, tools=True, structured_output=True),
    "anthropic": ProviderCapabilities(streaming=True, tools=True, token_usage=True),
    "azure_openai": ProviderCapabilities(streaming=True, tools=True),
    "vertex": ProviderCapabilities(streaming=True, tools=True, structured_output=True),
    "bedrock": ProviderCapabilities(streaming=False, tools=True, token_usage=True),
    "offline": ProviderCapabilities(streaming=True),
    "local": ProviderCapabilities(streaming=True),
}
