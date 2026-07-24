#!/usr/bin/env python3
"""RC IDs: RC-056, RC-062. Provide root workspace tasks and API drift checks."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from check_monorepo import validate_workspace

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
NPM = "npm.cmd" if os.name == "nt" else "npm"


def _run(*args: str, cwd: Path = REPOSITORY_ROOT) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def install() -> None:
    _run(sys.executable, "-m", "pip", "install", "-e", "backend[dev]")
    _run(sys.executable, "-m", "pip", "install", "-e", "packages/protocol")
    _run(NPM, "--prefix", "frontend", "install")


def generate_api() -> None:
    _run(sys.executable, "scripts/generate_api.py")


def check() -> None:
    errors = validate_workspace(REPOSITORY_ROOT)
    if errors:
        raise SystemExit("\n".join(f"ERROR: {error}" for error in errors))
    _run(sys.executable, "scripts/generate_api.py", "--check")
    _run(sys.executable, "scripts/check_rc_traceability.py", "--check")
    _run(sys.executable, "scripts/check_dependency_boundaries.py")
    _run(sys.executable, "scripts/check_model_distribution.py")
    _run(sys.executable, "scripts/check_rabbit_icon_language.py")
    _run(sys.executable, "scripts/check_rabbit_visual_regression.py", "--check")
    _run(sys.executable, "scripts/generate_design_tokens.py", "--check")
    _run(sys.executable, "scripts/check_rabbit_coverage_matrix.py", "--check")
    _run(sys.executable, "scripts/check_delivery_plan.py")
    _run(sys.executable, "scripts/generate_data_model.py", "--check")
    _run(sys.executable, "scripts/check_structured_logging.py")
    _run(sys.executable, "scripts/check_provider_privacy.py")
    _run(sys.executable, "scripts/check_metrics.py")


def test() -> None:
    _run(sys.executable, "-m", "pytest", "backend/tests", "-q")
    _run(NPM, "--prefix", "frontend", "test", "--", "--run")


def build() -> None:
    _run(NPM, "--prefix", "frontend", "run", "build")


def lint() -> None:
    _run(sys.executable, "-m", "ruff", "check", "backend", "scripts")
    _run(NPM, "--prefix", "frontend", "run", "lint")


def typecheck() -> None:
    _run(
        sys.executable,
        "-m",
        "mypy",
        "backend/src",
        "backend/rabbit_code",
    )
    _run(
        sys.executable,
        "-m",
        "mypy",
        "rabbit_code_protocol",
        cwd=REPOSITORY_ROOT / "packages" / "protocol",
    )


def verify() -> None:
    check()
    lint()
    typecheck()
    test()
    build()


COMMANDS = {
    "install": install,
    "generate-api": generate_api,
    "check": check,
    "test": test,
    "build": build,
    "lint": lint,
    "typecheck": typecheck,
    "verify": verify,
}


def main(argv: list[str] | None = None) -> int:
    command = (argv or sys.argv[1:])[:1]
    if not command or command[0] not in COMMANDS:
        choices = ", ".join(COMMANDS)
        print(f"Usage: python scripts/workspace.py <{choices}>")
        return 2
    COMMANDS[command[0]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
