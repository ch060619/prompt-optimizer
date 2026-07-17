from __future__ import annotations

from pathlib import Path

from scripts.check_desktop_boundary import validate_desktop_boundary

# RC ID: RC-060. Verify the desktop shell does not own Agent or Provider business logic.


def test_desktop_boundary_has_only_allowlisted_os_commands() -> None:
    repository_root = Path(__file__).resolve().parents[2]

    assert validate_desktop_boundary(repository_root) == []
