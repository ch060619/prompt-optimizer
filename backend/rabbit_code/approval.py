from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from time import monotonic
from typing import Any, Literal, cast
from uuid import uuid4

from packages.protocol.rabbit_code_protocol import ApprovalRequest

# RC ID: RC-202. Freeze dangerous tool requests before approval or execution.


class ApprovalError(PermissionError):
    """Base error for an approval request that cannot be executed."""


class ApprovalRequired(ApprovalError):
    def __init__(self, request: ApprovalRequest) -> None:
        super().__init__("dangerous operation requires approval")
        self.request = request


class ApprovalNotFound(ApprovalError):
    pass


class ApprovalExpired(ApprovalError):
    pass


class ApprovalDenied(ApprovalError):
    pass


class ApprovalMismatch(ApprovalError):
    pass


class ApprovalConsumed(ApprovalError):
    pass


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CONSUMED = "consumed"


@dataclass(frozen=True)
class _PendingApproval:
    request: ApprovalRequest
    deadline: float
    status: ApprovalStatus = ApprovalStatus.PENDING


class PermissionApprovalEngine:
    """Create, freeze, and consume one-shot approval requests."""

    def __init__(
        self,
        workspace_root: Path,
        *,
        timeout_seconds: float = 60.0,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.workspace_root = workspace_root.expanduser().resolve()
        if not self.workspace_root.is_dir():
            raise ValueError("workspace root must be a directory")
        self.timeout_seconds = timeout_seconds
        self._clock = clock
        self._pending: dict[str, _PendingApproval] = {}

    @property
    def pending(self) -> tuple[ApprovalRequest, ...]:
        return tuple(
            item.request
            for item in self._pending.values()
            if item.status is ApprovalStatus.PENDING
        )

    def request(
        self,
        *,
        tool: str,
        command: Sequence[str],
        paths: Sequence[str | Path] = (),
        workdir: str | Path = ".",
        impact: str,
        authorization_scope: str = "once",
        arguments: Mapping[str, Any] | None = None,
        description: str | None = None,
        risk: str = "high",
        request_id: str | None = None,
    ) -> ApprovalRequest:
        normalized_tool = _required_text(tool, "tool")
        normalized_command = _normalize_command(command)
        normalized_paths = [_normalize_path(self.workspace_root, path) for path in paths]
        normalized_workdir = _normalize_path(self.workspace_root, workdir)
        normalized_impact = _required_text(impact, "impact")
        normalized_scope = _required_text(authorization_scope, "authorization_scope")
        if risk not in {"low", "medium", "high"}:
            raise ValueError("risk must be low, medium, or high")
        frozen_arguments = copy.deepcopy(dict(arguments or {}))
        expires_at = datetime.now(UTC) + timedelta(seconds=self.timeout_seconds)
        request = ApprovalRequest(
            approval_id=uuid4().hex,
            request_id=request_id or uuid4().hex,
            action=normalized_tool,
            description=description or f"Approve {normalized_tool}",
            risk=cast(Literal["low", "medium", "high"], risk),
            tool=normalized_tool,
            command=list(normalized_command),
            paths=normalized_paths,
            workdir=normalized_workdir,
            impact=normalized_impact,
            authorization_scope=normalized_scope,
            arguments=frozen_arguments,
            expires_at=expires_at,
        )
        request = request.model_copy(update={"snapshot": _fingerprint(request)})
        self._pending[request.approval_id] = _PendingApproval(
            request=request,
            deadline=self._clock() + self.timeout_seconds,
        )
        return request

    def get(self, approval_id: str) -> ApprovalRequest:
        return self._entry(approval_id).request

    def status(self, approval_id: str) -> ApprovalStatus:
        entry = self._entry(approval_id)
        return self._current_entry(approval_id, entry).status

    def approve(
        self,
        approval_id: str,
        *,
        request: ApprovalRequest | None = None,
    ) -> ApprovalRequest:
        entry = self._current_entry(approval_id, self._entry(approval_id))
        self._assert_snapshot(entry.request, request)
        if entry.status is ApprovalStatus.EXPIRED:
            raise ApprovalExpired("approval request expired")
        if entry.status is not ApprovalStatus.PENDING:
            raise ApprovalError(f"approval is {entry.status.value}")
        self._pending[approval_id] = _PendingApproval(
            request=entry.request,
            deadline=entry.deadline,
            status=ApprovalStatus.APPROVED,
        )
        return entry.request

    def deny(
        self,
        approval_id: str,
        *,
        request: ApprovalRequest | None = None,
    ) -> ApprovalRequest:
        entry = self._current_entry(approval_id, self._entry(approval_id))
        self._assert_snapshot(entry.request, request)
        if entry.status is ApprovalStatus.EXPIRED:
            raise ApprovalExpired("approval request expired")
        if entry.status is not ApprovalStatus.PENDING:
            raise ApprovalError(f"approval is {entry.status.value}")
        self._pending[approval_id] = _PendingApproval(
            request=entry.request,
            deadline=entry.deadline,
            status=ApprovalStatus.DENIED,
        )
        return entry.request

    def execute(
        self,
        approval_id: str,
        executor: Callable[[], Any],
        *,
        request: ApprovalRequest | None = None,
    ) -> Any:
        entry = self._current_entry(approval_id, self._entry(approval_id))
        self._assert_snapshot(entry.request, request)
        if entry.status is ApprovalStatus.PENDING:
            raise ApprovalRequired(entry.request)
        if entry.status is ApprovalStatus.DENIED:
            raise ApprovalDenied("approval was denied")
        if entry.status is ApprovalStatus.EXPIRED:
            raise ApprovalExpired("approval request expired")
        if entry.status is ApprovalStatus.CONSUMED:
            raise ApprovalConsumed("approval was already consumed")
        self._pending[approval_id] = _PendingApproval(
            request=entry.request,
            deadline=entry.deadline,
            status=ApprovalStatus.CONSUMED,
        )
        return executor()

    def approve_and_execute(
        self,
        request: ApprovalRequest,
        executor: Callable[[], Any],
    ) -> Any:
        self.approve(request.approval_id, request=request)
        return self.execute(request.approval_id, executor, request=request)

    def _entry(self, approval_id: str) -> _PendingApproval:
        try:
            return self._pending[approval_id]
        except KeyError as exc:
            raise ApprovalNotFound(f"unknown approval request: {approval_id}") from exc

    def _current_entry(self, approval_id: str, entry: _PendingApproval) -> _PendingApproval:
        if entry.status is ApprovalStatus.PENDING and self._clock() >= entry.deadline:
            entry = _PendingApproval(
                request=entry.request,
                deadline=entry.deadline,
                status=ApprovalStatus.EXPIRED,
            )
            self._pending[approval_id] = entry
        return entry

    @staticmethod
    def _assert_snapshot(
        expected: ApprovalRequest,
        supplied: ApprovalRequest | None,
    ) -> None:
        if supplied is None:
            return
        if (
            supplied.approval_id != expected.approval_id
            or _fingerprint(supplied) != expected.snapshot
        ):
            raise ApprovalMismatch("approval snapshot no longer matches the requested operation")


def _required_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty")
    return value.strip()


def _normalize_command(command: Sequence[str]) -> tuple[str, ...]:
    if isinstance(command, str) or not command:
        raise ValueError("command must be a non-empty sequence")
    normalized = tuple(str(item) for item in command)
    if any(not item for item in normalized):
        raise ValueError("command arguments must not be empty")
    return normalized


def _normalize_path(workspace_root: Path, value: str | Path) -> str:
    raw = Path(value).expanduser()
    candidate = raw if raw.is_absolute() else workspace_root / raw
    return str(candidate.resolve(strict=False))


def _fingerprint(request: ApprovalRequest) -> str:
    payload = request.model_dump(mode="json", exclude={"snapshot"})
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
