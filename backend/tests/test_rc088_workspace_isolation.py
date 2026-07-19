from __future__ import annotations

from pathlib import Path

import pytest
from backend.rabbit_code.workspace_isolation import WorkspaceAccessError, WorkspaceManager

# RC ID: RC-088. Verify workspace, worktree, path, terminal, process, and cleanup boundaries.


def test_parallel_worktrees_cannot_cross_read_or_write(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    manager = WorkspaceManager()
    alice = manager.bind("alice", project, worktree_path=tmp_path / "worktrees" / "alice")
    bob = manager.bind("bob", project, worktree_path=tmp_path / "worktrees" / "bob")
    manager.write_text("alice", Path("task.txt"), "alice work")
    manager.write_text("bob", Path("task.txt"), "bob work")

    assert alice.workspace_id != bob.workspace_id
    assert manager.read_text("alice", Path("task.txt")) == "alice work"
    with pytest.raises(WorkspaceAccessError, match="outside"):
        manager.read_text("alice", bob.root / "task.txt")
    with pytest.raises(WorkspaceAccessError, match="outside"):
        manager.write_text("bob", alice.root / "task.txt", "cross-write")


def test_process_and_terminal_resources_cannot_be_mixed(tmp_path: Path) -> None:
    manager = WorkspaceManager()
    project = tmp_path / "project"
    project.mkdir()
    manager.bind("alice", project)
    manager.bind("bob", project)
    manager.register_process("alice", "process-1")
    manager.register_terminal("alice", "terminal-1")

    manager.assert_process_owner("alice", "process-1")
    manager.assert_terminal_owner("alice", "terminal-1")
    with pytest.raises(WorkspaceAccessError, match="another session"):
        manager.assert_process_owner("bob", "process-1")
    with pytest.raises(WorkspaceAccessError, match="another session"):
        manager.register_terminal("bob", "terminal-1")


def test_cleanup_removes_owned_worktree_and_cache_but_keeps_user_branch(tmp_path: Path) -> None:
    project = tmp_path / "project"
    branch = project / ".git" / "refs" / "heads" / "user-branch"
    branch.parent.mkdir(parents=True)
    branch.write_text("user commit", encoding="utf-8")
    worktree = tmp_path / "worktree"
    manager = WorkspaceManager()
    binding = manager.bind("alice", project, worktree_path=worktree)
    manager.write_text("alice", Path("task.txt"), "task")
    cache = manager.cache_path("alice", "result.json")
    cache.write_text("cache", encoding="utf-8")
    manager.register_process("alice", "process-1")
    manager.register_terminal("alice", "terminal-1")

    manager.cleanup("alice")

    assert binding.owns_root
    assert not worktree.exists()
    assert branch.read_text(encoding="utf-8") == "user commit"
    with pytest.raises(WorkspaceAccessError):
        manager.binding("alice")


def test_workspace_paths_and_ids_are_validated(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    manager = WorkspaceManager()
    manager.bind("alice", project)
    with pytest.raises(ValueError, match="invalid session_id"):
        manager.bind("bad/id", project)
    with pytest.raises(WorkspaceAccessError, match="outside"):
        manager.read_text("alice", tmp_path / "outside.txt")


def test_cleanup_does_not_remove_preexisting_project_cache(tmp_path: Path) -> None:
    project = tmp_path / "project"
    cache = project / ".rabbit-code" / "cache"
    cache.mkdir(parents=True)
    user_cache = cache / "user.json"
    user_cache.write_text("user cache", encoding="utf-8")
    manager = WorkspaceManager()
    manager.bind("alice", project)

    manager.cache_path("alice", "agent.json")
    manager.cleanup("alice")

    assert user_cache.read_text(encoding="utf-8") == "user cache"
