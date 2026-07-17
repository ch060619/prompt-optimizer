#!/usr/bin/env python3
"""RC ID: RC-056. Validate the root Rabbit Code workspace boundary."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

WORKSPACE_FILE = Path("workspace.toml")
BACKEND_PROJECT_FILE = Path("backend/pyproject.toml")
FRONTEND_PACKAGE_FILE = Path("frontend/package.json")
FRONTEND_LOCK_FILE = Path("frontend/package-lock.json")


def _read_toml(path: Path) -> dict[str, object]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_forbidden_imports(repository_root: Path) -> list[str]:
    errors: list[str] = []
    python_patterns = (
        re.compile(r"^(?:from|import)\s+(?:frontend|apps|packages)(?:\.|\s|$)"),
    )
    for source_root in (repository_root / "backend" / "src", repository_root / "scripts"):
        for path in source_root.rglob("*.py"):
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if any(pattern.match(line.strip()) for pattern in python_patterns):
                    relative_path = path.relative_to(repository_root).as_posix()
                    errors.append(f"cross-layer Python import: {relative_path}:{line_number}")
    return errors


def validate_workspace(repository_root: Path) -> list[str]:
    errors: list[str] = []
    workspace_path = repository_root / WORKSPACE_FILE
    if not workspace_path.is_file():
        return [f"missing workspace manifest: {WORKSPACE_FILE.as_posix()}"]

    workspace = _read_toml(workspace_path).get("workspace")
    if not isinstance(workspace, dict):
        return ["workspace.toml is missing the [workspace] table"]

    name = workspace.get("name")
    version = workspace.get("version")
    members = workspace.get("members")
    tasks = workspace.get("tasks")
    if name != "rabbit-code":
        errors.append("workspace name must be rabbit-code")
    if not isinstance(version, str) or not version:
        errors.append("workspace version must be a non-empty string")
    if not isinstance(members, list) or not all(isinstance(item, str) for item in members):
        errors.append("workspace members must be a list of paths")
        members = []
    if not isinstance(tasks, dict):
        errors.append("workspace.toml is missing the [workspace.tasks] table")
        tasks = {}

    for member in members:
        if not (repository_root / member).is_dir():
            errors.append(f"missing workspace member: {member}")
    for task in ("install", "check", "test", "build", "verify"):
        command = tasks.get(task)
        if not isinstance(command, str) or "scripts/workspace.py" not in command:
            errors.append(f"workspace task is missing or invalid: {task}")

    backend_project = repository_root / BACKEND_PROJECT_FILE
    frontend_package = repository_root / FRONTEND_PACKAGE_FILE
    frontend_lock = repository_root / FRONTEND_LOCK_FILE
    try:
        project = _read_toml(backend_project).get("project")
        package = _read_json(frontend_package)
        lock_packages = _read_json(frontend_lock).get("packages")
        if not isinstance(project, dict) or not isinstance(lock_packages, dict):
            raise TypeError("member metadata has an invalid object shape")
        lock_root = lock_packages.get("")
        if not isinstance(lock_root, dict):
            raise TypeError("frontend lockfile is missing its root package")
        backend_version = project["version"]
        frontend_version = package["version"]
        lock_version = lock_root["version"]
    except (KeyError, OSError, TypeError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        errors.append(f"unable to read member metadata: {exc}")
    else:
        if not (version == backend_version == frontend_version == lock_version):
            errors.append(
                "workspace, backend, frontend, and frontend lockfile versions must match"
            )

    errors.extend(_check_forbidden_imports(repository_root))
    return errors


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    errors = validate_workspace(repository_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Rabbit Code workspace manifest and boundaries are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
