from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

# RC ID: RC-183. Keep optional sync separate from local sessions and Provider credentials.


class SyncError(RuntimeError):
    """Base error for the opt-in synchronization boundary."""


class SyncDisabledError(SyncError):
    """Raised when local-only use attempts to call the optional sync service."""


class SyncAuthorizationError(SyncError):
    """Raised when enabled sync has not received explicit account authorization."""


class SyncTransport(Protocol):
    def push(self, payload: Mapping[str, object], *, account_token: str) -> None:
        ...


@dataclass(frozen=True)
class SyncStatus:
    enabled: bool
    account_required: bool
    local_only: bool


class OptionalSyncService:
    """A separately authorized, opt-in sync boundary; local use never needs it."""

    def __init__(self, *, enabled: bool = False, transport: SyncTransport | None = None) -> None:
        self.enabled = enabled
        self.transport = transport

    def status(self) -> SyncStatus:
        return SyncStatus(
            enabled=self.enabled,
            account_required=self.enabled,
            local_only=not self.enabled,
        )

    def push(self, payload: Mapping[str, object], *, account_token: str | None = None) -> None:
        if not self.enabled:
            raise SyncDisabledError("同步未启用；本地会话、模型和配置保持在本机。")
        if not account_token:
            raise SyncAuthorizationError("同步需要单独的账户授权。")
        if self.transport is None:
            raise SyncError("同步服务未配置。")
        self.transport.push(payload, account_token=account_token)
