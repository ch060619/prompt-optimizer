from __future__ import annotations

from pathlib import Path

from scripts.check_monorepo import validate_workspace

# RC ID: RC-056. Verify the root workspace manifest and dependency boundaries.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_workspace_manifest_has_all_declared_boundaries() -> None:
    assert validate_workspace(REPOSITORY_ROOT) == []
