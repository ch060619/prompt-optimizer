from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
from scripts.check_model_distribution import find_forbidden_weights

from prompt_optimizer.local_install import LocalInstallCore, LocalInstallError
from prompt_optimizer.model_manifest import (
    ModelManifestError,
    license_prompt,
    load_manifest,
    validate_license_confirmation,
)

# RC ID: RC-192. Verify weight-free distribution and explicit license confirmation.

ROOT = Path(__file__).parents[2]
MANIFEST = ROOT / "data/models/manifest.yml"


def test_manifest_requires_ondemand_license_review_before_download() -> None:
    models = load_manifest(MANIFEST)
    for model in models:
        prompt = license_prompt(model)
        assert prompt["distribution"] == "ondemand"
        assert prompt["summary"] == model.license_constraints
        assert prompt["license_url"] == model.license_url
        with pytest.raises(ModelManifestError, match="accepted"):
            validate_license_confirmation(model, accepted=False, confirmation_version=None)
        with pytest.raises(ModelManifestError, match="does not match"):
            validate_license_confirmation(model, accepted=True, confirmation_version="stale")
        validate_license_confirmation(
            model,
            accepted=True,
            confirmation_version=model.license_version,
        )


def test_install_state_records_license_confirmation_version(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"ondemand-model")
    core = LocalInstallCore(tmp_path / "install")
    core.start(
        model_id="Qwen-Qwen2.5-Coder-1.5B-Instruct",
        runner="ollama",
        source=source,
        checksum=hashlib.sha256(source.read_bytes()).hexdigest(),
        license_accepted=True,
        license_confirmation_version="Apache-2.0",
        license_url="https://www.apache.org/licenses/LICENSE-2.0",
        license_summary="Apache-2.0 terms apply to user downloads",
    )
    assert core.state is not None
    assert core.state.license_confirmation_version == "Apache-2.0"
    assert core.state.license_url == "https://www.apache.org/licenses/LICENSE-2.0"
    assert core.state.license_summary == "Apache-2.0 terms apply to user downloads"

    with pytest.raises(LocalInstallError, match="accepted"):
        LocalInstallCore(tmp_path / "other").start(
            model_id="Qwen-Qwen2.5-Coder-1.5B-Instruct",
            runner="ollama",
            source=source,
            checksum=hashlib.sha256(source.read_bytes()).hexdigest(),
            license_accepted=False,
        )


def test_distribution_check_rejects_weight_suffix_and_repo_is_weight_free(tmp_path: Path) -> None:
    forbidden = tmp_path / "weights.safetensors"
    forbidden.write_bytes(b"not a real model")
    command = [
        sys.executable,
        str(ROOT / "scripts/check_model_distribution.py"),
        "--root",
        str(tmp_path),
    ]
    rejected = subprocess.run(command, capture_output=True, text=True, check=False)
    assert rejected.returncode == 1
    assert "weights.safetensors" in rejected.stdout

    clean = subprocess.run(
        [*command[:-1], str(ROOT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert clean.returncode == 0, clean.stdout + clean.stderr


def test_distribution_check_ignores_only_cargo_target_artifacts(tmp_path: Path) -> None:
    cargo = tmp_path / "cargo"
    (cargo / "target").mkdir(parents=True)
    (cargo / "Cargo.toml").write_text("[package]\nname = \"fixture\"\n", encoding="utf-8")
    (cargo / "target" / "dep-graph.bin").write_bytes(b"cargo cache")
    unrelated = tmp_path / "target"
    unrelated.mkdir()
    forbidden = unrelated / "weights.bin"
    forbidden.write_bytes(b"model weight")

    assert find_forbidden_weights(tmp_path) == (forbidden.relative_to(tmp_path),)
