from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from packages.protocol.rabbit_code_protocol import ApprovalRequest

from .approval import PermissionApprovalEngine

# RC ID: RC-203. Store structured once, session, and matching-rule decisions.


class AuthorizationScope(StrEnum):
    ONCE = "once"
    SESSION = "session"
    RULE = "rule"


class CommandMatch(StrEnum):
    EXACT = "exact"
    PREFIX = "prefix"


class PathMatch(StrEnum):
    EXACT = "exact"
    WITHIN = "within"


@dataclass(frozen=True)
class AuthorizationRule:
    rule_id: str
    tool: str
    command: tuple[str, ...]
    paths: tuple[str, ...]
    workdir: str
    command_match: CommandMatch = CommandMatch.EXACT
    path_match: PathMatch = PathMatch.EXACT

    @classmethod
    def from_request(
        cls,
        request: ApprovalRequest,
        *,
        rule_id: str | None = None,
        command_match: CommandMatch = CommandMatch.EXACT,
        path_match: PathMatch = PathMatch.EXACT,
    ) -> AuthorizationRule:
        return cls(
            rule_id=rule_id or uuid4().hex,
            tool=request.tool,
            command=tuple(request.command),
            paths=tuple(request.paths),
            workdir=request.workdir,
            command_match=command_match,
            path_match=path_match,
        )

    def matches(self, request: ApprovalRequest) -> bool:
        if request.tool != self.tool or request.workdir != self.workdir:
            return False
        if self.command_match is CommandMatch.EXACT:
            if tuple(request.command) != self.command:
                return False
        elif tuple(request.command[: len(self.command)]) != self.command:
            return False
        if self.path_match is PathMatch.EXACT:
            return tuple(request.paths) == self.paths
        if not self.paths:
            return not request.paths
        return all(_within_any(path, self.paths) for path in request.paths)


@dataclass(frozen=True)
class AuthorizationGrant:
    grant_id: str
    scope: AuthorizationScope
    rule: AuthorizationRule | None
    session_id: str | None
    created_at: datetime
    revoked: bool = False


class AuthorizationStore:
    """Keep explicit grants separate from the one-shot approval engine."""

    def __init__(self, engine: PermissionApprovalEngine) -> None:
        self.engine = engine
        self._grants: dict[str, AuthorizationGrant] = {}

    @property
    def grants(self) -> tuple[AuthorizationGrant, ...]:
        return tuple(self._grants.values())

    def approve_once(self, request: ApprovalRequest) -> AuthorizationGrant:
        self.engine.approve(request.approval_id, request=request)
        return self._record(AuthorizationScope.ONCE, None, None)

    def approve_session(
        self,
        request: ApprovalRequest,
        *,
        session_id: str,
    ) -> AuthorizationGrant:
        normalized_session = _required_text(session_id, "session_id")
        rule = AuthorizationRule.from_request(request)
        grant = self._record(AuthorizationScope.SESSION, rule, normalized_session)
        try:
            self.engine.approve(request.approval_id, request=request)
        except Exception:
            self._grants.pop(grant.grant_id, None)
            raise
        return grant

    def approve_rule(
        self,
        request: ApprovalRequest,
        rule: AuthorizationRule,
    ) -> AuthorizationGrant:
        if not rule.matches(request):
            raise PermissionError("authorization rule does not match the request")
        grant = self._record(AuthorizationScope.RULE, rule, None)
        try:
            self.engine.approve(request.approval_id, request=request)
        except Exception:
            self._grants.pop(grant.grant_id, None)
            raise
        return grant

    def deny(self, request: ApprovalRequest, *, reason: str = "user denied") -> None:
        self.engine.deny(request.approval_id, request=request)

    def authorize(
        self,
        request: ApprovalRequest,
        *,
        session_id: str | None = None,
    ) -> AuthorizationGrant | None:
        grant = self._matching_grant(request, session_id=session_id)
        if grant is None:
            return None
        self.engine.approve(request.approval_id, request=request)
        return grant

    def edit_request(
        self,
        request: ApprovalRequest,
        *,
        command: Sequence[str] | None = None,
        paths: Sequence[str | Path] | None = None,
        workdir: str | Path | None = None,
        impact: str | None = None,
        arguments: Mapping[str, Any] | None = None,
    ) -> ApprovalRequest:
        if self.engine.status(request.approval_id).value == "pending":
            self.engine.deny(request.approval_id, request=request)
        next_arguments = dict(request.arguments) if arguments is None else dict(arguments)
        return self.engine.request(
            tool=request.tool,
            command=tuple(request.command) if command is None else command,
            paths=tuple(request.paths) if paths is None else paths,
            workdir=request.workdir if workdir is None else workdir,
            impact=request.impact if impact is None else impact,
            authorization_scope=AuthorizationScope.ONCE.value,
            arguments=next_arguments,
            description=request.description,
            risk=request.risk,
            request_id=request.request_id,
        )

    def revoke(self, grant_id: str) -> AuthorizationGrant:
        grant = self._grants.get(grant_id)
        if grant is None:
            raise KeyError(grant_id)
        revoked = replace(grant, revoked=True)
        self._grants[grant_id] = revoked
        return revoked

    def _matching_grant(
        self,
        request: ApprovalRequest,
        *,
        session_id: str | None,
    ) -> AuthorizationGrant | None:
        for grant in self._grants.values():
            if grant.revoked or grant.rule is None:
                continue
            if grant.scope is AuthorizationScope.SESSION and grant.session_id != session_id:
                continue
            if grant.rule.matches(request):
                return grant
        return None

    def _record(
        self,
        scope: AuthorizationScope,
        rule: AuthorizationRule | None,
        session_id: str | None,
    ) -> AuthorizationGrant:
        grant = AuthorizationGrant(
            grant_id=uuid4().hex,
            scope=scope,
            rule=rule,
            session_id=session_id,
            created_at=datetime.now(UTC),
        )
        self._grants[grant.grant_id] = grant
        return grant


def _required_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty")
    return value.strip()


def _within_any(path: str, prefixes: Sequence[str]) -> bool:
    candidate = Path(path)
    return any(_is_within(candidate, Path(prefix)) for prefix in prefixes)


def _is_within(path: Path, prefix: Path) -> bool:
    try:
        path.relative_to(prefix)
    except ValueError:
        return False
    return True
