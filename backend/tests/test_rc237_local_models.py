from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from prompt_optimizer.local_health import run_health_check
from prompt_optimizer.local_install import LocalInstallCore
from prompt_optimizer.model_lifecycle import ModelDirectoryService
from prompt_optimizer.model_manifest import gemma_model, load_manifest, qwen_coder_model
from prompt_optimizer.providers.base import ModelRequest
from prompt_optimizer.providers.local import LocalModelProvider
from prompt_optimizer.providers.runners import InMemoryRunnerAdapter

# RC ID: RC-237. Keep the CI local-model matrix fake, small, and weight-free.

MANIFEST = Path(__file__).parents[2] / "data/models/manifest.yml"
MODEL_CASES = (
    ("gemma", "gemma-3-1b-it", gemma_model),
    ("qwen", "qwen2.5-coder-1.5b-instruct", qwen_coder_model),
)


@pytest.mark.parametrize(("family", "install_id", "select_model"), MODEL_CASES)
def test_fake_runner_covers_both_model_families_end_to_end(
    tmp_path: Path,
    family: str,
    install_id: str,
    select_model,
) -> None:
    model = select_model(load_manifest(MANIFEST))
    source = tmp_path / f"{family}-tiny.weights"
    source.write_bytes((family.encode("ascii") + b"-fake-weight\n") * 32)
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    runner = InMemoryRunnerAdapter("ollama")
    runner.pull(model.model_id)

    core = LocalInstallCore(tmp_path / family)
    core.start(
        model_id=install_id,
        runner="ollama",
        source=source,
        checksum=checksum,
        license_accepted=True,
        health_check_required=True,
        license_confirmation_version=model.license_status,
        license_summary="test-only metadata; no model weights are committed",
    )
    core.download_step(max_bytes=8)
    core.pause()
    resumed = LocalInstallCore(tmp_path / family)
    resumed.resume()
    while resumed.state is not None and resumed.state.phase == "download":
        resumed.download_step(max_bytes=8)
    assert resumed.verify()["event"] == "verified"
    assert resumed.install()["event"] == "installed"

    report = run_health_check(
        runner,
        model_id=model.model_id,
        context_length=8,
        report_path=tmp_path / f"{family}-health.json",
        resource_probe=lambda: 128,
        state_recorder=resumed,
    )
    assert report.ready is True
    provider = LocalModelProvider(runner)
    result = provider.optimize(ModelRequest(prompt=f"Run the {family} fake model smoke."))
    assert result.analysis.optimized_prompt
    assert resumed.run()["event"] == "running"


@pytest.mark.parametrize(
    ("family", "model_id"),
    (("gemma", "gemma-3-1b-it"), ("qwen", "qwen2.5-coder-1.5b-instruct")),
)
def test_model_directory_repairs_corruption_and_preserves_uninstall_history(
    tmp_path: Path,
    family: str,
    model_id: str,
) -> None:
    source = tmp_path / f"{family}-source.bin"
    source.write_bytes(f"{family}-model".encode("ascii"))
    service = ModelDirectoryService(
        tmp_path / f"{family}-registry.json", tmp_path / f"{family}-models"
    )
    service.install_version(
        model_id=model_id,
        source=source,
        version="v1",
        checksum=hashlib.sha256(source.read_bytes()).hexdigest(),
    )

    service.active_path(model_id).write_bytes(b"corrupt")
    repaired = service.repair(model_id, source=source)
    assert repaired.repaired is True
    assert service.active_path(model_id).read_bytes() == source.read_bytes()

    result = service.uninstall(model_id)
    assert result.deleted is True
    assert result.history_preserved is True
