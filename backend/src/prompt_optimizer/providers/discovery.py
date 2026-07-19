from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from time import monotonic

import httpx

from prompt_optimizer.providers.base import ProviderConfig
from prompt_optimizer.providers.presets import get_preset

# RC ID: RC-168. Discover model IDs without replacing user-entered model choices.

MODEL_ID_PATTERN = re.compile(r"^[^\s\x00-\x1f\x7f]{1,256}$")


@dataclass(frozen=True)
class ModelDiscoveryResult:
    models: tuple[str, ...]
    error_code: str | None = None
    from_cache: bool = False

    @property
    def succeeded(self) -> bool:
        return self.error_code is None


@dataclass(frozen=True)
class _CachedModels:
    models: tuple[str, ...]
    expires_at: float


class _DiscoveryResponseError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class ModelDiscoveryService:
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        ttl_seconds: float = 300.0,
        max_pages: int = 20,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero")
        if max_pages <= 0:
            raise ValueError("max_pages must be greater than zero")
        self.client = client or httpx.Client()
        self.ttl_seconds = ttl_seconds
        self.max_pages = max_pages
        self._clock = clock
        self._cache: dict[tuple[str, str], _CachedModels] = {}

    def discover(
        self,
        config: ProviderConfig,
        *,
        stored_models: Sequence[str] = (),
        manual_model: str | None = None,
        force: bool = False,
    ) -> ModelDiscoveryResult:
        preset = get_preset(config.name)
        models_from_user = _valid_models((*stored_models, manual_model or ""))
        if preset is None or not preset.model_discovery_path:
            return ModelDiscoveryResult(models_from_user, error_code="unsupported")
        base_url = (config.base_url or preset.base_url).rstrip("/")
        endpoint = f"{base_url}{preset.model_discovery_path}"
        key = (config.name.lower(), endpoint)
        now = self._clock()
        cached = self._cache.get(key)
        if cached is not None and not force and now < cached.expires_at:
            return ModelDiscoveryResult(
                _merge_models(cached.models, models_from_user),
                from_cache=True,
            )

        try:
            models = self._fetch_models(config, endpoint)
        except _DiscoveryResponseError as exc:
            if cached is not None:
                return ModelDiscoveryResult(
                    _merge_models(cached.models, models_from_user),
                    error_code=exc.code,
                    from_cache=True,
                )
            return ModelDiscoveryResult(models_from_user, error_code=exc.code)
        except httpx.TimeoutException:
            return self._failed_result(cached, models_from_user, "timeout")
        except httpx.HTTPError:
            return self._failed_result(cached, models_from_user, "network")
        except (TypeError, ValueError):
            return self._failed_result(cached, models_from_user, "invalid_response")

        self._cache[key] = _CachedModels(models=models, expires_at=now + self.ttl_seconds)
        return ModelDiscoveryResult(_merge_models(models, models_from_user))

    def clear(self, provider_name: str | None = None) -> None:
        if provider_name is None:
            self._cache.clear()
            return
        normalized = provider_name.lower()
        self._cache = {
            key: value for key, value in self._cache.items() if key[0] != normalized
        }

    def _failed_result(
        self,
        cached: _CachedModels | None,
        user_models: Sequence[str],
        error_code: str,
    ) -> ModelDiscoveryResult:
        models = cached.models if cached is not None else ()
        return ModelDiscoveryResult(
            _merge_models(models, user_models),
            error_code=error_code,
            from_cache=cached is not None,
        )

    def _fetch_models(self, config: ProviderConfig, endpoint: str) -> tuple[str, ...]:
        headers = {
            "Accept": "application/json",
        }
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
        headers.update(dict(config.custom_headers))
        models: list[str] = []
        cursor: str | None = None
        seen_cursors: set[str] = set()
        for page in range(self.max_pages):
            params = {"cursor": cursor} if cursor is not None else None
            response = self.client.get(endpoint, headers=headers, params=params)
            if response.status_code == 401:
                raise _DiscoveryResponseError("unauthorized")
            if response.status_code == 403:
                raise _DiscoveryResponseError("forbidden")
            if response.status_code == 429:
                raise _DiscoveryResponseError("rate_limit")
            if response.status_code >= 400:
                raise _DiscoveryResponseError("server")
            payload = response.json()
            models.extend(_extract_model_ids(payload))
            next_cursor = _next_cursor(payload)
            if next_cursor is None or next_cursor in seen_cursors:
                break
            seen_cursors.add(next_cursor)
            cursor = next_cursor
            if page == self.max_pages - 1:
                break
        return _unique_models(models)


def validate_model_id(value: str) -> bool:
    return bool(MODEL_ID_PATTERN.fullmatch(value))


def _valid_models(values: Iterable[str]) -> tuple[str, ...]:
    return _unique_models(value.strip() for value in values if validate_model_id(value.strip()))


def _merge_models(*groups: Iterable[str]) -> tuple[str, ...]:
    return _unique_models(value for group in groups for value in group)


def _unique_models(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if validate_model_id(value)))


def _extract_model_ids(payload: object) -> tuple[str, ...]:
    entries: object
    if isinstance(payload, list):
        entries = payload
    elif isinstance(payload, dict):
        entries = payload["data"] if "data" in payload else payload.get("models")
        if not isinstance(entries, list):
            raise ValueError("model discovery response has no model list")
    else:
        raise ValueError("model discovery response is not an object or list")
    model_ids: list[str] = []
    for entry in entries:
        if isinstance(entry, str):
            model_id = entry
        elif isinstance(entry, dict):
            value = entry.get("id") or entry.get("name") or entry.get("model")
            model_id = value if isinstance(value, str) else ""
        else:
            model_id = ""
        if validate_model_id(model_id):
            model_ids.append(model_id)
    return tuple(model_ids)


def _next_cursor(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("next_cursor", "nextCursor", "cursor"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    next_page = payload.get("next_page")
    if isinstance(next_page, str) and next_page:
        return next_page
    return None
