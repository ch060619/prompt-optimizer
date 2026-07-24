"""RC ID: RC-274. Validate reproducible packaging setup."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIDECAR_SPEC = ROOT / "apps" / "desktop" / "sidecar.spec"
BUILD_SCRIPT = ROOT / "scripts" / "build_reproducible.py"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc274_reproducible.py"
FRONTEND_LOCK = ROOT / "frontend" / "package-lock.json"


def test_sidecar_spec_exists() -> None:
    assert SIDECAR_SPEC.is_file()


def test_sidecar_spec_no_upx() -> None:
    content = SIDECAR_SPEC.read_text(encoding="utf-8")
    assert "upx=False" in content


def test_sidecar_spec_no_strip() -> None:
    content = SIDECAR_SPEC.read_text(encoding="utf-8")
    assert "strip=False" in content


def test_sidecar_spec_names_output() -> None:
    content = SIDECAR_SPEC.read_text(encoding="utf-8")
    assert "rabbit-sidecar" in content


def test_sidecar_spec_has_uvicorn() -> None:
    content = SIDECAR_SPEC.read_text(encoding="utf-8")
    assert "uvicorn" in content


def test_sidecar_spec_has_prompt_optimizer() -> None:
    content = SIDECAR_SPEC.read_text(encoding="utf-8")
    assert "prompt_optimizer" in content


def test_build_script_exists() -> None:
    assert BUILD_SCRIPT.is_file()


def test_build_script_has_source_date_epoch() -> None:
    content = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert "SOURCE_DATE_EPOCH" in content


def test_build_script_has_manifest() -> None:
    content = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert "build_manifest" in content or "build-manifest" in content


def test_build_script_has_sha256() -> None:
    content = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert "_sha256" in content


def test_frontend_lock_exists() -> None:
    assert FRONTEND_LOCK.is_file()


def test_check_script_exists() -> None:
    assert CHECK_SCRIPT.is_file()
