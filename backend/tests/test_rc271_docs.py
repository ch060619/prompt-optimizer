from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_documentation_gate_passes_and_has_marked_smoke_commands() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_docs.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "documents" in result.stdout


def test_marked_smoke_commands_run_without_network_or_destructive_flags() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_docs.py", "--run"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Ran 3 marked smoke command(s)." in result.stdout
