"""RC ID: RC-273. Validate CLI installation channels."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "backend" / "pyproject.toml"
INSTALL_PS1 = ROOT / "scripts" / "install" / "install.ps1"
INSTALL_SH = ROOT / "scripts" / "install" / "install.sh"
WINGET_YML = ROOT / "scripts" / "install" / "winget.yml"
SCOOP_JSON = ROOT / "scripts" / "install" / "scoop.json"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc273_cli_channels.py"


def test_pyproject_pypi_config() -> None:
    """pyproject.toml must define rabbit-code package with entry points."""
    content = PYPROJECT.read_text(encoding="utf-8")
    assert 'name = "rabbit-code"' in content
    assert "rabbit = " in content
    assert "prompt-opt = " in content


def test_install_ps1_exists() -> None:
    assert INSTALL_PS1.is_file()
    content = INSTALL_PS1.read_text(encoding="utf-8")
    assert "rabbit-code" in content
    assert "pip install" in content


def test_install_sh_exists() -> None:
    assert INSTALL_SH.is_file()
    content = INSTALL_SH.read_text(encoding="utf-8")
    assert "rabbit-code" in content
    assert "pip install" in content


def test_winget_manifest() -> None:
    assert WINGET_YML.is_file()
    content = WINGET_YML.read_text(encoding="utf-8")
    assert "RabbitCode.RabbitCode" in content
    assert "MIT" in content


def test_scoop_manifest() -> None:
    assert SCOOP_JSON.is_file()
    scoop = json.loads(SCOOP_JSON.read_text(encoding="utf-8"))
    assert scoop["version"] == "3.0.0"
    assert "rabbit" in scoop["bin"]
    assert scoop["license"] == "MIT"


def test_check_script_exists() -> None:
    assert CHECK_SCRIPT.is_file()
