from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from backend.rabbit_code.git_tools import GitTools, RemoteWriteDenied
from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy

# RC ID: RC-092. Verify local Git operations, worktrees, conflicts, and remote authorization.


def _git(repo: Path, *args: str) -> None:
    subprocess.run(("git", *args), cwd=repo, check=True, capture_output=True)


def _tools(tmp_path: Path) -> GitTools:
    if shutil.which("git") is None:
        pytest.skip("git is unavailable")
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    policy = PermissionPolicy(repo)
    policy.switch_mode(PermissionMode.EDIT, explicit_confirmation=True)
    return GitTools(repo, permission_policy=policy)


def test_git_status_diff_stage_commit_log_and_unicode_paths(tmp_path: Path) -> None:
    tools = _tools(tmp_path)
    file_path = tools.repository / "中文 name.txt"
    file_path.write_text("before\n", encoding="utf-8")
    initial = tools.status()
    assert "中文 name.txt" in initial.untracked
    tools.stage((file_path,))
    tools.commit("initial")

    file_path.write_text("after\n", encoding="utf-8")
    assert "after" in tools.diff(path=file_path)
    tools.stage(("中文 name.txt",))
    committed = tools.commit("update")
    assert committed.returncode == 0
    assert tools.log(limit=2)[0].subject == "update"
    assert tools.status().dirty is False
    assert any(branch.current for branch in tools.branches())


def test_git_worktree_remove_keeps_branch_and_conflicts_are_reported(tmp_path: Path) -> None:
    tools = _tools(tmp_path)
    file_path = tools.repository / "file.txt"
    file_path.write_text("base\n", encoding="utf-8")
    tools.stage((file_path,))
    tools.commit("base")
    tools.create_branch("feature")
    worktree = tmp_path / "feature-worktree"
    tools.add_worktree(worktree, "feature")
    assert any(item.path == worktree.resolve() for item in tools.worktrees())
    tools.remove_worktree(worktree)
    assert not worktree.exists()
    assert any(branch.name == "feature" for branch in tools.branches())


def test_git_conflict_helper_reports_unmerged_paths(tmp_path: Path) -> None:
    tools = _tools(tmp_path)
    file_path = tools.repository / "conflict.txt"
    file_path.write_text("base\n", encoding="utf-8")
    tools.stage((file_path,))
    tools.commit("base")
    tools.create_branch("feature")
    _git(tools.repository, "switch", "feature")
    file_path.write_text("feature\n", encoding="utf-8")
    tools.stage((file_path,))
    tools.commit("feature")
    _git(tools.repository, "switch", "main")
    file_path.write_text("main\n", encoding="utf-8")
    tools.stage((file_path,))
    tools.commit("main")
    merge = subprocess.run(
        ("git", "merge", "feature"),
        cwd=tools.repository,
        capture_output=True,
    )
    assert merge.returncode != 0
    assert tools.conflicts() == ("conflict.txt",)
    _git(tools.repository, "merge", "--abort")


def test_remote_writes_are_denied_and_audited_without_authorization(tmp_path: Path) -> None:
    tools = _tools(tmp_path)
    with pytest.raises(RemoteWriteDenied, match="explicit authorization"):
        tools.push()
    with pytest.raises(RemoteWriteDenied, match="explicit authorization"):
        tools.create_pr("title")
    assert [(event.action, event.allowed) for event in tools.remote_audit] == [
        ("push", False),
        ("pull_request", False),
    ]


def test_git_paths_and_repository_state_are_checked(tmp_path: Path) -> None:
    tools = _tools(tmp_path)
    with pytest.raises(ValueError, match="within"):
        tools.diff(path=tmp_path / "outside.txt")
    with pytest.raises(ValueError, match="positive"):
        tools.log(limit=0)
    with pytest.raises(PermissionError, match="read-only"):
        policy = PermissionPolicy(tools.repository)
        GitTools(tools.repository, permission_policy=policy).stage(("new.txt",))
