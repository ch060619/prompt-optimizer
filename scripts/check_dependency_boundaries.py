#!/usr/bin/env python3
"""RC ID: RC-066. Enforce replaceable provider boundaries at UI and route surfaces."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

SURFACE_DIRECTORIES = (
    Path("backend/src/prompt_optimizer/api"),
    Path("backend/src/prompt_optimizer/cli"),
    Path("frontend/src"),
)
PROVIDER_IMPLEMENTATION_MODULES = {
    "prompt_optimizer.providers.offline",
    "prompt_optimizer.providers.openai",
    "prompt_optimizer.providers.http",
    "prompt_optimizer.providers.registry",
}
CONCRETE_PROVIDER_NAMES = {
    "OfflineRuleProvider",
    "OpenAICompatibleAdapter",
    "HttpChatProvider",
    "ProviderRegistry",
}


def _iter_source_files(repository_root: Path):
    for relative_directory in SURFACE_DIRECTORIES:
        directory = repository_root / relative_directory
        if not directory.is_dir():
            continue
        yield from directory.rglob("*.py")
        yield from directory.rglob("*.ts")
        yield from directory.rglob("*.tsx")
        yield from directory.rglob("*.js")
        yield from directory.rglob("*.jsx")


def _module_name(node: ast.ImportFrom) -> str:
    return node.module or ""


def _check_python(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        return [f"unable to parse {path}: {exc}"]

    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = _module_name(node)
            if module in PROVIDER_IMPLEMENTATION_MODULES:
                errors.append(f"surface imports provider implementation: {path}:{node.lineno}")
            if any(alias.name in CONCRETE_PROVIDER_NAMES for alias in node.names):
                errors.append(f"surface imports concrete provider: {path}:{node.lineno}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in PROVIDER_IMPLEMENTATION_MODULES:
                    errors.append(f"surface imports provider implementation: {path}:{node.lineno}")
        elif isinstance(node, ast.Call):
            function_name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if function_name in CONCRETE_PROVIDER_NAMES:
                errors.append(f"surface constructs concrete provider: {path}:{node.lineno}")
    return errors


def _check_typescript(path: Path) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if any(module in line for module in PROVIDER_IMPLEMENTATION_MODULES):
            errors.append(f"surface imports provider implementation: {path}:{line_number}")
    return errors


def validate_dependency_boundaries(repository_root: Path) -> list[str]:
    errors: list[str] = []
    for path in _iter_source_files(repository_root):
        if path.suffix == ".py":
            errors.extend(_check_python(path))
        else:
            errors.extend(_check_typescript(path))
    return errors


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    errors = validate_dependency_boundaries(repository_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("RC-066 dependency boundaries are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
