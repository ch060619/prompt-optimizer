"""RC ID: RC-272. Validate desktop installer build configuration and artifacts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAURI_CONF = ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"
BUILD_SCRIPT = ROOT / "scripts" / "build_desktop.py"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc272_desktop_build.py"


def test_tauri_bundle_active() -> None:
    """bundle.active must be true for release builds."""
    conf = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
    assert conf["bundle"]["active"] is True


def test_tauri_targets_all() -> None:
    """bundle.targets must be 'all' to cover Windows and Linux."""
    conf = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
    assert conf["bundle"]["targets"] == "all"


def test_tauri_icons_exist() -> None:
    """All configured icon files must exist."""
    conf = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
    for icon in conf["bundle"]["icon"]:
        icon_path = ROOT / "apps" / "desktop" / "src-tauri" / icon
        assert icon_path.is_file(), f"missing icon: {icon}"


def test_tauri_metadata_set() -> None:
    """Publisher, category, descriptions must be set."""
    conf = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
    b = conf["bundle"]
    assert b["publisher"]
    assert b["category"]
    assert b["shortDescription"]
    assert b["longDescription"]


def test_no_macos_bundle() -> None:
    """macOS must not be configured (explicitly excluded)."""
    conf = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
    assert "macOS" not in conf.get("bundle", {})


def test_identifier_set() -> None:
    """Application identifier must be set."""
    conf = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
    assert conf["identifier"] == "com.rabbitcode.desktop"


def test_windows_bundle_config() -> None:
    """Windows must have nsis or wix configured."""
    conf = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
    win = conf["bundle"].get("windows", {})
    assert "nsis" in win or "wix" in win


def test_linux_bundle_config() -> None:
    """Linux must have deb configured."""
    conf = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
    linux = conf["bundle"].get("linux", {})
    assert "deb" in linux


def test_build_script_exists() -> None:
    """Build script must exist."""
    assert BUILD_SCRIPT.is_file()


def test_check_script_exists() -> None:
    """Check script must exist."""
    assert CHECK_SCRIPT.is_file()
