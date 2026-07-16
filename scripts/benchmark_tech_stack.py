#!/usr/bin/env python3
"""RC ID: RC-046. Capture reproducible local metrics for the stack retention ADR."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from types import ModuleType
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SIDECAR_PATH = REPOSITORY_ROOT / "scripts" / "prototypes" / "sidecar_probe.py"


def _load_sidecar_probe() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sidecar_probe", SIDECAR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SIDECAR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _command_output(command: list[str], timeout: float = 10.0) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            env={**os.environ, "NO_COLOR": "1"},
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {
            "available": False,
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
            "summary": type(exc).__name__,
        }
    output = (result.stdout or result.stderr).strip().splitlines()
    return {
        "available": result.returncode == 0,
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
        "summary": output[0] if output else f"exit {result.returncode}",
    }


def _sqlite_benchmark(row_count: int = 5_000) -> dict[str, int | str]:
    connection = sqlite3.connect(":memory:")
    started = time.perf_counter()
    with connection:
        connection.execute("CREATE TABLE benchmark (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        connection.executemany(
            "INSERT INTO benchmark(value) VALUES (?)",
            ((f"value-{index}",) for index in range(row_count)),
        )
    write_ms = int((time.perf_counter() - started) * 1000)
    started = time.perf_counter()
    count = int(connection.execute("SELECT COUNT(*) FROM benchmark").fetchone()[0])
    read_ms = int((time.perf_counter() - started) * 1000)
    connection.close()
    return {
        "sqlite_version": sqlite3.sqlite_version,
        "rows": count,
        "transactional_write_ms": write_ms,
        "count_read_ms": read_ms,
    }


def _frontend_dist() -> dict[str, int]:
    dist = REPOSITORY_ROOT / "frontend" / "dist"
    files = [path for path in dist.rglob("*") if path.is_file()] if dist.is_dir() else []
    return {"files": len(files), "bytes": sum(path.stat().st_size for path in files)}


def collect_metrics() -> dict[str, Any]:
    sidecar_probe = _load_sidecar_probe()
    with tempfile.TemporaryDirectory(prefix="rabbit-stack-benchmark-") as directory:
        sidecar = sidecar_probe.run_probe(
            python_executable=sys.executable,
            data_dir=Path(directory),
            timeout_seconds=10.0,
        )

    return {
        "rc_id": "RC-046",
        "captured_at": datetime.now(UTC).isoformat(),
        "git_commit": _command_output(["git", "rev-parse", "HEAD"])["summary"],
        "platform": platform.platform(),
        "versions": {
            "python": platform.python_version(),
            "fastapi": version("fastapi"),
            "uvicorn": version("uvicorn"),
            "typer": version("typer"),
            "react": _command_output(
                ["node", "-p", "require('./frontend/node_modules/react/package.json').version"]
            )["summary"],
            "vite": _command_output(
                ["node", "-p", "require('./frontend/node_modules/vite/package.json').version"]
            )["summary"],
            "typescript": _command_output(
                [
                    "node",
                    "-p",
                    "require('./frontend/node_modules/typescript/package.json').version",
                ]
            )["summary"],
            "docker_cli": _command_output(["docker", "--version"]),
            "docker_server": _command_output(
                ["docker", "info", "--format", "{{.ServerVersion}}"], timeout=5.0
            ),
        },
        "sidecar": sidecar,
        "sqlite": _sqlite_benchmark(),
        "typer_help": _command_output(
            [sys.executable, "-m", "prompt_optimizer.cli", "--help"]
        ),
        "frontend_dist": _frontend_dist(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write JSON to this path")
    args = parser.parse_args(argv)

    payload = json.dumps(collect_metrics(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(args.output.as_posix())
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
