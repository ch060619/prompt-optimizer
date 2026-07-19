from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ModelSelectionScope = Literal["global", "workspace", "session", "optimizer"]


@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model: str | None = None


class ModelSelectionStore:
    """Keep model routes separate by scope without storing credentials."""

    def __init__(
        self,
        *,
        global_path: Path | None = None,
        workspace_path: Path | None = None,
    ) -> None:
        self.global_path = global_path
        self.workspace_path = workspace_path
        self._routes: dict[ModelSelectionScope, ModelRoute | None] = {
            "global": self._load(global_path),
            "workspace": self._load(workspace_path),
            "session": None,
            "optimizer": None,
        }

    def set(
        self,
        scope: ModelSelectionScope,
        provider: str,
        model: str | None = None,
    ) -> ModelRoute:
        route = ModelRoute(provider=provider.strip(), model=model.strip() if model else None)
        if not route.provider:
            raise ValueError("model route provider cannot be empty")
        self._routes[scope] = route
        if scope == "global":
            self._save(self.global_path, route)
        elif scope == "workspace":
            self._save(self.workspace_path, route)
        return route

    def clear(self, scope: ModelSelectionScope) -> None:
        self._routes[scope] = None
        path = self.global_path if scope == "global" else self.workspace_path
        if scope in {"global", "workspace"} and path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                raise ValueError(f"unable to clear model route: {path}") from exc

    def route(self, scope: ModelSelectionScope) -> ModelRoute | None:
        return self._routes[scope]

    def resolve_session(
        self,
        *,
        provider: str | None,
        model: str | None,
    ) -> tuple[ModelRoute, Literal["global", "workspace", "session", "default"]]:
        if provider is not None or model is not None:
            base = self._routes["session"] or ModelRoute(provider or "offline")
            return ModelRoute(provider or base.provider, model or base.model), "session"
        for scope in ("session", "workspace", "global"):
            route = self._routes[scope]
            if route is not None:
                return route, scope
        return ModelRoute("offline"), "default"

    def resolve_optimizer(
        self,
        *,
        provider: str | None,
        model: str | None,
        session: ModelRoute,
    ) -> ModelRoute | None:
        if provider is not None or model is not None:
            return ModelRoute(provider or session.provider, model or session.model)
        return self._routes["optimizer"]

    @staticmethod
    def _load(path: Path | None) -> ModelRoute | None:
        if path is None or not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"unable to read model route: {path}") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("provider"), str):
            raise ValueError(f"model route must contain a provider: {path}")
        model = payload.get("model")
        return ModelRoute(payload["provider"], model if isinstance(model, str) else None)

    @staticmethod
    def _save(path: Path | None, route: ModelRoute) -> None:
        if path is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {"provider": route.provider, "model": route.model},
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise ValueError(f"unable to save model route: {path}") from exc
