from __future__ import annotations

import json
from dataclasses import dataclass, replace
from enum import StrEnum
from uuid import uuid4

# RC ID: RC-086. Provide bounded session lifecycle operations with audit history.


class SessionAction(StrEnum):
    CREATE = "create"
    READ = "read"
    LIST = "list"
    SEARCH = "search"
    RENAME = "rename"
    PIN = "pin"
    ARCHIVE = "archive"
    DELETE = "delete"
    RESTORE = "restore"
    CONTINUE = "continue"
    FORK = "fork"
    EXPORT = "export"


@dataclass(frozen=True)
class SessionRecord:
    id: str
    owner_id: str
    title: str
    messages: tuple[str, ...] = ()
    pinned: bool = False
    archived: bool = False
    deleted: bool = False
    parent_id: str | None = None


@dataclass(frozen=True)
class SessionPage:
    items: tuple[SessionRecord, ...]
    offset: int
    limit: int
    total: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total


@dataclass(frozen=True)
class SessionAuditEvent:
    sequence: int
    actor_id: str
    action: SessionAction
    session_id: str | None = None
    related_session_id: str | None = None


@dataclass(frozen=True)
class AuditPage:
    events: tuple[SessionAuditEvent, ...]
    offset: int
    limit: int
    total: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.events) < self.total


class SessionStore:
    """In-process session service; soft-deleted records remain recoverable."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}
        self._audit: list[SessionAuditEvent] = []

    def create(
        self,
        owner_id: str,
        title: str,
        messages: tuple[str, ...] = (),
    ) -> SessionRecord:
        owner_id = _require_text(owner_id, "owner_id")
        session = SessionRecord(
            id=uuid4().hex,
            owner_id=owner_id,
            title=_require_text(title, "title"),
            messages=_messages(messages),
        )
        self._sessions[session.id] = session
        self._record(owner_id, SessionAction.CREATE, session.id)
        return session

    def get(self, owner_id: str, session_id: str) -> SessionRecord:
        session = self._owned(owner_id, session_id)
        self._record(owner_id, SessionAction.READ, session.id)
        return session

    def list_sessions(
        self,
        owner_id: str,
        *,
        offset: int = 0,
        limit: int = 50,
        include_deleted: bool = False,
    ) -> SessionPage:
        owner_id = _require_text(owner_id, "owner_id")
        offset, limit = _page_bounds(offset, limit)
        sessions = self._visible(owner_id, include_deleted=include_deleted)
        self._record(owner_id, SessionAction.LIST)
        return _page(sessions, offset, limit)

    def search(
        self,
        owner_id: str,
        query: str,
        *,
        offset: int = 0,
        limit: int = 50,
        include_deleted: bool = False,
    ) -> SessionPage:
        owner_id = _require_text(owner_id, "owner_id")
        query = _require_text(query, "query").casefold()
        offset, limit = _page_bounds(offset, limit)
        sessions = tuple(
            session
            for session in self._visible(owner_id, include_deleted=include_deleted)
            if query in session.title.casefold()
            or any(query in message.casefold() for message in session.messages)
        )
        self._record(owner_id, SessionAction.SEARCH)
        return _page(sessions, offset, limit)

    def rename(self, owner_id: str, session_id: str, title: str) -> SessionRecord:
        session = self._owned(owner_id, session_id)
        updated = replace(session, title=_require_text(title, "title"))
        self._sessions[session.id] = updated
        self._record(owner_id, SessionAction.RENAME, session.id)
        return updated

    def pin(self, owner_id: str, session_id: str, pinned: bool = True) -> SessionRecord:
        session = self._owned(owner_id, session_id)
        updated = replace(session, pinned=pinned)
        self._sessions[session.id] = updated
        self._record(owner_id, SessionAction.PIN, session.id)
        return updated

    def archive(self, owner_id: str, session_id: str, archived: bool = True) -> SessionRecord:
        session = self._owned(owner_id, session_id)
        updated = replace(session, archived=archived)
        self._sessions[session.id] = updated
        self._record(owner_id, SessionAction.ARCHIVE, session.id)
        return updated

    def delete(self, owner_id: str, session_id: str) -> SessionRecord:
        session = self._owned(owner_id, session_id)
        updated = replace(session, deleted=True)
        self._sessions[session.id] = updated
        self._record(owner_id, SessionAction.DELETE, session.id)
        return updated

    def restore(self, owner_id: str, session_id: str) -> SessionRecord:
        session = self._owned(owner_id, session_id, include_deleted=True)
        updated = replace(session, deleted=False)
        self._sessions[session.id] = updated
        self._record(owner_id, SessionAction.RESTORE, session.id)
        return updated

    def continue_session(self, owner_id: str, session_id: str) -> SessionRecord:
        session = self._owned(owner_id, session_id)
        updated = replace(session, archived=False)
        self._sessions[session.id] = updated
        self._record(owner_id, SessionAction.CONTINUE, session.id)
        return updated

    def fork(self, owner_id: str, session_id: str, *, title: str | None = None) -> SessionRecord:
        session = self._owned(owner_id, session_id)
        forked = SessionRecord(
            id=uuid4().hex,
            owner_id=session.owner_id,
            title=_require_text(title, "title") if title is not None else f"{session.title} (fork)",
            messages=session.messages,
            parent_id=session.id,
        )
        self._sessions[forked.id] = forked
        self._record(owner_id, SessionAction.FORK, forked.id, related_session_id=session.id)
        return forked

    def export(self, owner_id: str, session_id: str) -> str:
        session = self._owned(owner_id, session_id)
        self._record(owner_id, SessionAction.EXPORT, session.id)
        return json.dumps(
            {
                "id": session.id,
                "owner_id": session.owner_id,
                "title": session.title,
                "messages": list(session.messages),
                "pinned": session.pinned,
                "archived": session.archived,
                "deleted": session.deleted,
                "parent_id": session.parent_id,
            },
            ensure_ascii=False,
            sort_keys=True,
        )

    def audit_page(self, *, offset: int = 0, limit: int = 50) -> AuditPage:
        offset, limit = _page_bounds(offset, limit)
        return AuditPage(
            events=tuple(self._audit[offset : offset + limit]),
            offset=offset,
            limit=limit,
            total=len(self._audit),
        )

    def _owned(
        self,
        owner_id: str,
        session_id: str,
        *,
        include_deleted: bool = False,
    ) -> SessionRecord:
        owner_id = _require_text(owner_id, "owner_id")
        session_id = _require_text(session_id, "session_id")
        session = self._sessions.get(session_id)
        if session is None or session.owner_id != owner_id:
            raise KeyError(f"session not found: {session_id}")
        if session.deleted and not include_deleted:
            raise KeyError(f"session not found: {session_id}")
        return session

    def _visible(self, owner_id: str, *, include_deleted: bool) -> tuple[SessionRecord, ...]:
        return tuple(
            session
            for session in self._sessions.values()
            if session.owner_id == owner_id and (include_deleted or not session.deleted)
        )

    def _record(
        self,
        actor_id: str,
        action: SessionAction,
        session_id: str | None = None,
        *,
        related_session_id: str | None = None,
    ) -> None:
        self._audit.append(
            SessionAuditEvent(
                sequence=len(self._audit),
                actor_id=actor_id,
                action=action,
                session_id=session_id,
                related_session_id=related_session_id,
            )
        )


def _page_bounds(offset: int, limit: int) -> tuple[int, int]:
    if offset < 0 or limit < 1:
        raise ValueError("offset must be non-negative and limit must be positive")
    return offset, limit


def _page(items: tuple[SessionRecord, ...], offset: int, limit: int) -> SessionPage:
    return SessionPage(items[offset : offset + limit], offset, limit, len(items))


def _messages(messages: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(messages, tuple):
        raise TypeError("messages must be a tuple of strings")
    if any(not isinstance(message, str) for message in messages):
        raise ValueError("messages must contain strings")
    return messages


def _require_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value
