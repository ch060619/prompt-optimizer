from __future__ import annotations

from pathlib import Path

from scripts.check_desktop_boundary import validate_desktop_boundary

# RC ID: RC-060. Verify the desktop shell does not own Agent or Provider business logic.


def test_desktop_boundary_has_only_allowlisted_os_commands() -> None:
    repository_root = Path(__file__).resolve().parents[2]

    assert validate_desktop_boundary(repository_root) == []


def test_desktop_boundary_ignores_generated_rust_target(tmp_path: Path) -> None:
    desktop = tmp_path / "apps" / "desktop"
    desktop.mkdir(parents=True)
    (desktop / "command-allowlist.toml").write_text(
        """[desktop]
business_logic = false

[[commands]]
name = "open_window"
[[commands]]
name = "pick_file"
[[commands]]
name = "notify"
[[commands]]
name = "check_update"
[[commands]]
name = "store_secret"
[[commands]]
name = "start_sidecar"
""",
        encoding="utf-8",
    )
    generated = desktop / "src-tauri" / "target" / "generated.rs"
    generated.parent.mkdir(parents=True)
    generated.write_text("Provider AgentCore prompt_optimizer", encoding="utf-8")

    assert validate_desktop_boundary(tmp_path) == []
