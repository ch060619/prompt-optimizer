from __future__ import annotations

import pytest
from backend.rabbit_code.memory import MemoryScope, MemoryScopeDisabled, MemoryStore

# RC ID: RC-085. Verify isolated scopes, confirmation, lifecycle operations, and disablement.


def test_memory_tables_isolate_scope_and_scope_id() -> None:
    store = MemoryStore()
    temporary = store.write(
        MemoryScope.TEMPORARY,
        "run-1",
        "temporary context",
        source="terminal",
        purpose="current request",
        confirmed=True,
    )
    session = store.write(
        MemoryScope.SESSION,
        "session-1",
        "session fact",
        source="conversation",
        purpose="resume session",
        confirmed=True,
    )
    project = store.write(
        MemoryScope.PROJECT,
        "project-a",
        "project convention",
        source="AGENTS.md",
        purpose="project task context",
        confirmed=True,
    )
    store.write(
        MemoryScope.PROJECT,
        "project-b",
        "other project convention",
        source="AGENTS.md",
        purpose="other project task context",
        confirmed=True,
    )

    assert store.list(MemoryScope.TEMPORARY, "run-1") == (temporary,)
    assert store.list(MemoryScope.SESSION, "session-1") == (session,)
    assert store.list(MemoryScope.PROJECT, "project-a") == (project,)
    assert store.list(MemoryScope.PROJECT, "project-b")[0].content == "other project convention"
    assert store.list(MemoryScope.USER, "user-1") == ()


def test_memory_write_and_edit_require_source_purpose_confirmation() -> None:
    store = MemoryStore()

    with pytest.raises(PermissionError, match="source and purpose"):
        store.write(
            MemoryScope.USER,
            "user-1",
            "preferred format",
            source="conversation",
            purpose="personalize responses",
        )
    with pytest.raises(ValueError, match="source"):
        store.write(
            MemoryScope.USER,
            "user-1",
            "preferred format",
            source=" ",
            purpose="personalize responses",
            confirmed=True,
        )

    entry = store.write(
        MemoryScope.USER,
        "user-1",
        "preferred format",
        source="conversation",
        purpose="personalize responses",
        confirmed=True,
    )
    with pytest.raises(PermissionError, match="source and purpose"):
        store.edit(
            MemoryScope.USER,
            "user-1",
            entry.id,
            "updated format",
            source="conversation",
            purpose="personalize responses",
        )


def test_disabled_scope_rejects_reads_and_writes() -> None:
    store = MemoryStore()
    entry = store.write(
        MemoryScope.SESSION,
        "session-1",
        "fact",
        source="conversation",
        purpose="resume session",
        confirmed=True,
    )
    store.set_enabled(MemoryScope.SESSION, "session-1", False)

    with pytest.raises(MemoryScopeDisabled):
        store.list(MemoryScope.SESSION, "session-1")
    with pytest.raises(MemoryScopeDisabled):
        store.get(MemoryScope.SESSION, "session-1", entry.id)
    with pytest.raises(MemoryScopeDisabled):
        store.write(
            MemoryScope.SESSION,
            "session-1",
            "new fact",
            source="conversation",
            purpose="resume session",
            confirmed=True,
        )
    with pytest.raises(MemoryScopeDisabled):
        store.edit(
            MemoryScope.SESSION,
            "session-1",
            entry.id,
            "updated fact",
            source="conversation",
            purpose="resume session",
            confirmed=True,
        )
    with pytest.raises(MemoryScopeDisabled):
        store.delete(MemoryScope.SESSION, "session-1", entry.id)
    with pytest.raises(MemoryScopeDisabled):
        store.clear(MemoryScope.SESSION, "session-1")

    store.set_enabled(MemoryScope.SESSION, "session-1", True)
    assert store.get(MemoryScope.SESSION, "session-1", entry.id) == entry


def test_memory_supports_edit_delete_scope_clear_and_global_clear() -> None:
    store = MemoryStore()
    entry = store.write(
        MemoryScope.PROJECT,
        "project-a",
        "old convention",
        source="README.md",
        purpose="project context",
        confirmed=True,
    )
    updated = store.edit(
        MemoryScope.PROJECT,
        "project-a",
        entry.id,
        "new convention",
        source="AGENTS.md",
        purpose="project context",
        confirmed=True,
    )
    assert store.get(MemoryScope.PROJECT, "project-a", entry.id) == updated

    store.delete(MemoryScope.PROJECT, "project-a", entry.id)
    assert store.list(MemoryScope.PROJECT, "project-a") == ()
    store.write(
        MemoryScope.TEMPORARY,
        "run-1",
        "temporary",
        source="terminal",
        purpose="current request",
        confirmed=True,
    )
    store.write(
        MemoryScope.USER,
        "user-1",
        "preference",
        source="conversation",
        purpose="personalize responses",
        confirmed=True,
    )
    store.clear_all()

    assert store.list(MemoryScope.TEMPORARY, "run-1") == ()
    assert store.list(MemoryScope.USER, "user-1") == ()
