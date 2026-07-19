from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from enum import StrEnum
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from prompt_optimizer.identity import DISTRIBUTION_NAME
from prompt_optimizer.paths import app_data_dir, default_db_path

# RC ID: RC-108. Provide safe CLI completion, diagnostics, path/version checks, and cleanup.


EXPECTED_VERSION = "3.0.0"
_SAFE_DATA_DIR_NAMES = frozenset({"rabbit-code", "prompt-optimizer"})
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class CompletionShell(StrEnum):
    BASH = "bash"
    ZSH = "zsh"
    FISH = "fish"
    POWERSHELL = "powershell"


@dataclass(frozen=True)
class InstallationPaths:
    executable: Path | None
    package_root: Path
    data_dir: Path
    database_path: Path

    def to_dict(self) -> dict[str, str | None]:
        return {
            "executable": str(self.executable) if self.executable else None,
            "package_root": str(self.package_root),
            "data_dir": str(self.data_dir),
            "database_path": str(self.database_path),
        }


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass(frozen=True)
class DoctorReport:
    version: str
    paths: InstallationPaths
    checks: tuple[DoctorCheck, ...]

    @property
    def ok(self) -> bool:
        return all(check.status != "error" for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "ok": self.ok,
            "paths": self.paths.to_dict(),
            "checks": [check.to_dict() for check in self.checks],
        }


@dataclass(frozen=True)
class UninstallPlan:
    data_dir: Path
    cache_paths: tuple[Path, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "data_dir": str(self.data_dir),
            "cache_paths": [str(path) for path in self.cache_paths],
            "purge_data_requires_confirmation": True,
        }


def package_version() -> str:
    try:
        return version(DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return EXPECTED_VERSION


def installation_paths(*, data_dir: Path | None = None) -> InstallationPaths:
    resolved_data_dir = (
        data_dir.expanduser().resolve() if data_dir is not None else app_data_dir().resolve()
    )
    database_path = (
        resolved_data_dir / "rabbit-code.sqlite3"
        if data_dir is not None
        else default_db_path().resolve()
    )
    executable = shutil.which("rabbit")
    return InstallationPaths(
        executable=Path(executable).resolve() if executable else None,
        package_root=Path(__file__).resolve().parent,
        data_dir=resolved_data_dir,
        database_path=database_path,
    )


def build_doctor_report(*, data_dir: Path | None = None) -> DoctorReport:
    paths = installation_paths(data_dir=data_dir)
    checks = [
        _python_check(),
        _package_check(),
        DoctorCheck(
            "executable",
            "ok" if paths.executable else "warn",
            str(paths.executable) if paths.executable else "rabbit executable is not on PATH",
        ),
        _directory_check(paths.data_dir),
        _parent_directory_check("database", paths.database_path),
    ]
    return DoctorReport(package_version(), paths, tuple(checks))


def build_uninstall_plan(*, data_dir: Path | None = None) -> UninstallPlan:
    resolved = (
        data_dir.expanduser().resolve()
        if data_dir is not None
        else installation_paths().data_dir
    )
    _validate_data_dir(resolved)
    cache_paths = tuple(
        path
        for path in (resolved / "cache", resolved / "logs", resolved / "tmp")
        if path.exists()
    )
    return UninstallPlan(resolved, cache_paths)


def execute_uninstall(
    plan: UninstallPlan,
    *,
    purge_data: bool = False,
    confirmed: bool = False,
) -> tuple[Path, ...]:
    if not confirmed:
        raise PermissionError("uninstall confirmation is required")
    targets = (plan.data_dir,) if purge_data else plan.cache_paths
    removed: list[Path] = []
    for target in targets:
        if target.is_dir():
            shutil.rmtree(target)
            removed.append(target)
        elif target.exists():
            target.unlink()
            removed.append(target)
    return tuple(removed)


def render_completion(shell: CompletionShell | str) -> str:
    selected = CompletionShell(shell)
    return {
        CompletionShell.BASH: _bash_completion(),
        CompletionShell.ZSH: _zsh_completion(),
        CompletionShell.FISH: _fish_completion(),
        CompletionShell.POWERSHELL: _powershell_completion(),
    }[selected]


def _python_check() -> DoctorCheck:
    current = sys.version_info[:2]
    status = "ok" if current >= (3, 12) else "error"
    return DoctorCheck("python", status, f"Python {current[0]}.{current[1]}")


def _package_check() -> DoctorCheck:
    current = package_version()
    status = "ok" if current == EXPECTED_VERSION else "warn"
    return DoctorCheck("package", status, f"Rabbit Code {current}")


def _directory_check(path: Path) -> DoctorCheck:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return DoctorCheck("data_dir", "error", f"cannot create {path}: {exc}")
    return DoctorCheck("data_dir", "ok", str(path))


def _parent_directory_check(name: str, path: Path) -> DoctorCheck:
    status = "ok" if path.parent.is_dir() else "error"
    detail = str(path) if status == "ok" else f"parent does not exist: {path.parent}"
    return DoctorCheck(name, status, detail)


def _validate_data_dir(path: Path) -> None:
    if path.name not in _SAFE_DATA_DIR_NAMES:
        raise ValueError("path is not a Rabbit Code data directory")
    if path == _PROJECT_ROOT or _PROJECT_ROOT.is_relative_to(path):
        raise ValueError("Rabbit Code data directory cannot contain the project workspace")
    if path == Path(path.anchor):
        raise ValueError("Rabbit Code data directory cannot be a filesystem root")


def _commands() -> str:
    return (
        "analyze optimize run templates history config serve completion doctor "
        "version path uninstall"
    )


def _bash_completion() -> str:
    return (
        "_rabbit_completion() {\n"
        "  local cur=\"${COMP_WORDS[COMP_CWORD]}\"\n"
        f"  COMPREPLY=( $(compgen -W \"{_commands()}\" -- \"$cur\") )\n"
        "}\n"
        "complete -F _rabbit_completion rabbit\n"
    )


def _zsh_completion() -> str:
    return (
        "#compdef rabbit\n"
        "_rabbit() {\n"
        f"  _arguments '1:command:(({_commands()}))'\n"
        "}\n"
        "compdef _rabbit rabbit\n"
    )


def _fish_completion() -> str:
    return "\n".join(
        f"complete -c rabbit -f -n '__fish_use_subcommand' -a '{command}'"
        for command in _commands().split()
    ) + "\n"


def _powershell_completion() -> str:
    commands = "', '".join(_commands().split())
    return (
        "Register-ArgumentCompleter -Native -CommandName rabbit -ScriptBlock {\n"
        "  param($wordToComplete)\n"
        f"  @('{commands}') | "
        "Where-Object { $_ -like \"$wordToComplete*\" } | "
        "ForEach-Object { [System.Management.Automation.CompletionResult]::new("
        "$_, $_, 'ParameterValue', $_) }\n"
        "}\n"
    )
