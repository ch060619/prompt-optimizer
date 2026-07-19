from __future__ import annotations

from pathlib import Path

import pytest

from prompt_optimizer.model_manifest import (
    HardwareCapacity,
    ModelManifestError,
    gemma_model,
    is_known_model,
    load_manifest,
    qwen_coder_model,
    recommend_models,
)

# RC ID: RC-188. Verify controlled models, safe recommendations, and unknown-model policy.

ROOT = Path(__file__).parents[2]
MANIFEST = ROOT / "data/models/manifest.yml"


def test_manifest_loads_fixed_models_and_recommends_with_safety_margin() -> None:
    models = load_manifest(MANIFEST)
    assert {model.family for model in models} == {"Gemma", "Qwen2.5-Coder"}
    assert gemma_model(models).model_id == "google/gemma-3-1b-it"
    assert qwen_coder_model(models).model_id == "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    assert all(model.source_url.startswith("https://") for model in models)
    assert all(len(model.file_sha256) == 64 for model in models)

    recommendations = recommend_models(
        models,
        HardwareCapacity(
            ram_bytes=8 * 1024**3,
            disk_free_bytes=16 * 1024**3,
            vram_bytes=4 * 1024**3,
        ),
    )
    assert all(item.recommended for item in recommendations)
    assert all("license_confirmation_required" in item.reasons for item in recommendations)


def test_capacity_limits_and_unknown_model_policy_are_fail_closed() -> None:
    models = load_manifest(MANIFEST)
    recommendations = recommend_models(
        models,
        HardwareCapacity(
            ram_bytes=2 * 1024**3,
            disk_free_bytes=2 * 1024**3,
            vram_bytes=1 * 1024**3,
        ),
    )
    assert all(not item.recommended for item in recommendations)
    assert all("ram_exceeds_safe_margin" in item.reasons for item in recommendations)
    assert is_known_model(models[0].model_id, models)
    assert not is_known_model("unknown/model", models)
    assert is_known_model("unknown/model", models, advanced=True)


def test_manifest_rejects_invalid_hash_and_non_https_source(tmp_path: Path) -> None:
    invalid = MANIFEST.read_text(encoding="utf-8").replace(
        "https://huggingface.co", "http://huggingface.co", 1
    )
    invalid = invalid.replace(
        "3d4ef8d71c14db7e448a09ebe891cfb6bf32c57a9b44499ae0d1c098e48516b6",
        "bad",
        1,
    )
    path = tmp_path / "manifest.yml"
    path.write_text(invalid, encoding="utf-8")

    with pytest.raises(ModelManifestError):
        load_manifest(path)
