from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .permissions import CapabilityDomain, PermissionPolicy

# RC ID: RC-092. Provide structured local Git operations and explicit remote authorization.


class GitRepositoryError(RuntimeError):
    pass


class GitCommandError(GitRepositoryError):
    def __init__(self, result: GitResult) -> None:
        super().__init__(f"git command failed ({result.returncode}): {' '.join(result.args)}")
        self.result = result


class RemoteWriteDenied(PermissionError):
    pass


@dataclass(frozen=True)
class GitResult:
    args: tuple[str, ...]
    stdout: str
    stderr: str
    returncode: int


@dataclass(frozen=True)
class GitStatus:
    branch: str | None
    staged: tuple[str, ...]
    unstaged: tuple[str, ...]
    untracked: tuple[str, ...]
    conflicted: tuple[str, ...]

    @property
    def dirty(self) -> bool:
        return bool(self.staged or self.unstaged or self.untracked or self.conflicted)


@dataclass(frozen=True)
class GitLogEntry:
    commit: str
    author: str
    date: str
    subject: str


@dataclass(frozen=True)
class GitBranch:
    name: str
    current: bool


@dataclass(frozen=True)
class GitWorktree:
    path: Path
    commit: str | None
    branch: str | None


@dataclass(frozen=True)
class RemoteWriteAudit:
    action: str
    allowed: bool
    reason: str


class GitTools:
    def __init__(
        self,
        repository: Path,
        *,
        permission_policy: PermissionPolicy | None = None,
    ) -> None:
        candidate = repository.expanduser().resolve()
        if not candidate.is_dir():
            raise ValueError("repository must be a directory")
        self.repository = self._discover_root(candidate)
        self.permission_policy = permission_policy or PermissionPolicy(self.repository)
        self._remote_audit: list[RemoteWriteAudit] = []

    @property
    def remote_audit(self) -> tuple[RemoteWriteAudit, ...]:
        return tuple(self._remote_audit)

    def status(self) -> GitStatus:
        branch_result = self._run(("symbolic-ref", "--short", "HEAD"), check=False)
        branch = branch_result.stdout.strip() or None
        result = self._run(("status", "--porcelain=v1", "-z", "--untracked-files=all"))
        staged: list[str] = []
        unstaged: list[str] = []
        untracked: list[str] = []
        conflicted: list[str] = []
        for item in result.stdout.split("\x00"):
            if not item:
                continue
            if item.startswith("?? "):
                untracked.append(item[3:])
                continue
            if len(item) < 4:
                continue
            code = item[:2]
            path = item[3:]
            if code[0] != " ":
                staged.append(path)
            if code[1] != " ":
                unstaged.append(path)
            if code in {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}:
                conflicted.append(path)
        return GitStatus(
            branch,
            tuple(staged),
            tuple(unstaged),
            tuple(untracked),
            tuple(conflicted),
        )

    def diff(self, *, cached: bool = False, path: str | Path | None = None) -> str:
        args = ["diff"]
        if cached:
            args.append("--cached")
        if path is not None:
            args.extend(("--", self._relative_path(path)))
        return self._run(tuple(args)).stdout

    def log(self, *, limit: int = 50) -> tuple[GitLogEntry, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        result = self._run(
            (
                "log",
                f"-{limit}",
                "--date=iso-strict",
                "--format=%H%x00%an%x00%ad%x00%s",
            )
        )
        entries: list[GitLogEntry] = []
        for line in result.stdout.splitlines():
            fields = line.split("\x00", 3)
            if len(fields) == 4:
                entries.append(GitLogEntry(*fields))
        return tuple(entries)

    def branches(self) -> tuple[GitBranch, ...]:
        current = self.status().branch
        result = self._run(("branch", "--format=%(refname:short)"))
        return tuple(
            GitBranch(name, name == current)
            for name in result.stdout.splitlines()
            if name
        )

    def worktrees(self) -> tuple[GitWorktree, ...]:
        result = self._run(("worktree", "list", "--porcelain"))
        worktrees: list[GitWorktree] = []
        current_path: Path | None = None
        current_commit: str | None = None
        current_branch: str | None = None
        for line in result.stdout.splitlines() + [""]:
            if line == "":
                if current_path is not None:
                    worktrees.append(GitWorktree(current_path, current_commit, current_branch))
                current_path = None
                current_commit = None
                current_branch = None
                continue
            key, _, value = line.partition(" ")
            if key == "worktree":
                current_path = Path(value).resolve()
            elif key == "HEAD":
                current_commit = value
            elif key == "branch":
                current_branch = value.removeprefix("refs/heads/")
        return tuple(worktrees)

    def stage(self, paths: Sequence[str | Path]) -> GitResult:
        relative_paths = self._relative_paths(paths)
        self._authorize_write()
        return self._run(("add", "--", *relative_paths))

    def create_branch(self, name: str, *, start_point: str | None = None) -> GitResult:
        name = _require_text(name, "branch name")
        self._authorize_write()
        args = ["branch", name]
        if start_point is not None:
            args.append(start_point)
        return self._run(tuple(args))

    def add_worktree(self, path: Path, branch: str, *, create_branch: bool = False) -> GitResult:
        path = path.expanduser().resolve()
        if path.exists():
            raise FileExistsError(path)
        branch = _require_text(branch, "branch name")
        self._authorize_write()
        path.parent.mkdir(parents=True, exist_ok=True)
        args = ["worktree", "add"]
        if create_branch:
            args.extend(("-b", branch))
            args.append(str(path))
        else:
            args.extend((str(path), branch))
        return self._run(tuple(args))

    def remove_worktree(self, path: Path, *, force: bool = False) -> GitResult:
        resolved = path.expanduser().resolve()
        self._authorize_write()
        args = ["worktree", "remove"]
        if force:
            args.append("--force")
        args.append(str(resolved))
        return self._run(tuple(args))

    def commit(self, message: str) -> GitResult:
        message = _require_text(message, "commit message")
        self._authorize_write()
        cached = self._run(("diff", "--cached", "--quiet"), check=False)
        if cached.returncode == 0:
            raise GitRepositoryError("no staged changes to commit")
        return self._run(("commit", "-m", message))

    def conflicts(self) -> tuple[str, ...]:
        return self.status().conflicted

    def push(
        self,
        remote: str = "origin",
        branch: str | None = None,
        *,
        remote_authorized: bool = False,
    ) -> GitResult:
        if not remote_authorized:
            return self._deny_remote("push")
        args = ["push", remote]
        if branch is not None:
            args.append(branch)
        self._remote_audit.append(RemoteWriteAudit("push", True, "explicit remote authorization"))
        return self._run(tuple(args))

    def create_pr(
        self,
        title: str,
        body: str = "",
        *,
        remote_authorized: bool = False,
    ) -> GitResult:
        if not remote_authorized:
            return self._deny_remote("pull_request")
        self._remote_audit.append(
            RemoteWriteAudit("pull_request", True, "explicit remote authorization")
        )
        return self._run(("gh", "pr", "create", "--title", title, "--body", body))

    def _deny_remote(self, action: str) -> GitResult:
        reason = "remote writes require explicit authorization"
        self._remote_audit.append(RemoteWriteAudit(action, False, reason))
        raise RemoteWriteDenied(reason)

    def _authorize_write(self) -> None:
        decision = self.permission_policy.authorize_capability(
            CapabilityDomain.GIT,
            "write",
            {"path": self.repository},
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)

    def _run(self, args: Sequence[str], *, check: bool = True) -> GitResult:
        normalized = ("git", *tuple(args))
        completed = subprocess.run(
            normalized,
            cwd=self.repository,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        result = GitResult(normalized, completed.stdout, completed.stderr, completed.returncode)
        if check and result.returncode != 0:
            raise GitCommandError(result)
        return result

    def _relative_paths(self, paths: Sequence[str | Path]) -> tuple[str, ...]:
        normalized = tuple(self._relative_path(path) for path in paths)
        if not normalized:
            raise ValueError("at least one path is required")
        return normalized

    def _relative_path(self, path: str | Path) -> str:
        candidate = Path(path).expanduser()
        resolved = (candidate if candidate.is_absolute() else self.repository / candidate).resolve()
        try:
            return resolved.relative_to(self.repository).as_posix()
        except ValueError as exc:
            raise ValueError("Git path must remain within the repository") from exc

    @staticmethod
    def _discover_root(candidate: Path) -> Path:
        result = subprocess.run(
            ("git", "rev-parse", "--show-toplevel"),
            cwd=candidate,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            raise GitRepositoryError("path is not a Git repository")
        return Path(result.stdout.strip()).resolve()


def _require_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value
