from __future__ import annotations

import json

import pytest
from backend.rabbit_code.sessions import SessionAction, SessionStore

# RC ID: RC-086. Verify session CRUD, pagination, lifecycle, fork, export, and audit history.


def test_sessions_support_crud_search_and_paginated_audit() -> None:
    store = SessionStore()
    first = store.create("alice", "Alpha task", ("find alpha",))
    second = store.create("alice", "Beta task", ("find beta",))
    store.create("bob", "Alice private task", ("not visible",))

    assert store.get("alice", first.id) == first
    assert store.rename("alice", first.id, "Renamed task").title == "Renamed task"
    assert store.pin("alice", first.id).pinned
    assert store.archive("alice", second.id).archived
    assert [session.title for session in store.search("alice", "renamed").items] == [
        "Renamed task"
    ]

    page = store.list_sessions("alice", offset=0, limit=1)
    assert page.items[0].id == first.id
    assert page.total == 2
    assert page.has_more
    assert store.list_sessions("bob").total == 1
    with pytest.raises(KeyError):
        store.get("bob", first.id)

    audit = store.audit_page(offset=0, limit=3)
    assert len(audit.events) == 3
    assert audit.has_more
    assert audit.events[0].action is SessionAction.CREATE


def test_soft_delete_restore_and_continue_preserve_session() -> None:
    store = SessionStore()
    session = store.create("alice", "Recoverable", ("message",))
    store.archive("alice", session.id)
    continued = store.continue_session("alice", session.id)
    assert not continued.archived

    deleted = store.delete("alice", session.id)
    assert deleted.deleted
    assert store.list_sessions("alice").items == ()
    with pytest.raises(KeyError):
        store.continue_session("alice", session.id)

    restored = store.restore("alice", session.id)
    assert not restored.deleted
    assert store.get("alice", session.id).messages == ("message",)
    assert store.list_sessions("alice", include_deleted=True).total == 1


def test_fork_copies_content_without_mutating_original_and_export_is_json() -> None:
    store = SessionStore()
    original = store.create("alice", "Original", ("one", "two"))
    forked = store.fork("alice", original.id, title="Branch")

    assert forked.id != original.id
    assert forked.parent_id == original.id
    assert forked.messages == original.messages
    assert store.get("alice", original.id) == original
    assert json.loads(store.export("alice", forked.id)) == {
        "id": forked.id,
        "owner_id": "alice",
        "title": "Branch",
        "messages": ["one", "two"],
        "pinned": False,
        "archived": False,
        "deleted": False,
        "parent_id": original.id,
    }
    fork_event = next(
        event for event in store.audit_page().events if event.action is SessionAction.FORK
    )
    assert fork_event.action is SessionAction.FORK
    assert fork_event.related_session_id == original.id
    assert store.audit_page().events[-1].action is SessionAction.EXPORT


def test_session_inputs_and_pagination_are_bounded() -> None:
    store = SessionStore()
    with pytest.raises(ValueError, match="title"):
        store.create("alice", " ")
    with pytest.raises(TypeError, match="tuple"):
        store.create("alice", "title", ["message"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="limit"):
        store.list_sessions("alice", limit=0)
