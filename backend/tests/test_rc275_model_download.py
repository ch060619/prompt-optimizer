"""RC ID: RC-275. Validate local model on-demand download policy."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAURI_CONF = ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"
SIDECAR_SPEC = ROOT / "apps" / "desktop" / "sidecar.spec"
LOCAL_INSTALL = ROOT / "backend" / "src" / "prompt_optimizer" / "local_install.py"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc275_model_download.py"

MODEL_WEIGHT_EXTS = [".gguf", ".safetensors", ".onnx", ".tflite", ".ckpt"]


def test_tauri_conf_no_model_weights() -> None:
    content = TAURI_CONF.read_text(encoding="utf-8")
    for ext in MODEL_WEIGHT_EXTS:
        assert ext not in content.lower()


def test_sidecar_spec_no_model_weights() -> None:
    content = SIDECAR_SPEC.read_text(encoding="utf-8")
    for ext in MODEL_WEIGHT_EXTS:
        assert ext not in content.lower()


def test_local_install_has_checksum() -> None:
    content = LOCAL_INSTALL.read_text(encoding="utf-8")
    assert "checksum" in content


def test_local_install_has_hashlib() -> None:
    content = LOCAL_INSTALL.read_text(encoding="utf-8")
    assert "hashlib" in content or "sha256" in content.lower()


def test_local_install_has_download() -> None:
    content = LOCAL_INSTALL.read_text(encoding="utf-8")
    assert "download" in content.lower()


def test_local_install_has_retry() -> None:
    content = LOCAL_INSTALL.read_text(encoding="utf-8")
    assert "retr" in content.lower()


def test_local_install_has_failure_handling() -> None:
    content = LOCAL_INSTALL.read_text(encoding="utf-8")
    assert "failed" in content


def test_no_model_weights_in_source() -> None:
    for pattern in ["*.gguf", "*.safetensors", "*.onnx", "*.tflite", "*.ckpt"]:
        for f in ROOT.rglob(pattern):
            rel = str(f.relative_to(ROOT))
            assert ".venv" in rel or "node_modules" in rel, f"model weight found: {rel}"


def test_check_script_exists() -> None:
    assert CHECK_SCRIPT.is_file()
