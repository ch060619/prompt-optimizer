from __future__ import annotations

from pathlib import Path

from prompt_optimizer.model_manifest import gemma_model, load_manifest
from prompt_optimizer.providers.base import ModelRequest
from prompt_optimizer.providers.local import LocalModelProvider
from prompt_optimizer.providers.runners import InMemoryRunnerAdapter

# RC ID: RC-190. Verify the fixed Gemma release, template/EOS metadata, and smoke path.

MANIFEST = Path(__file__).parents[2] / "data/models/manifest.yml"


def test_gemma_release_is_fixed_and_generation_smoke_is_bound_to_it() -> None:
    model = gemma_model(load_manifest(MANIFEST))
    assert model.model_id == "google/gemma-3-1b-it"
    assert model.chat_template == "gemma-3"
    assert model.eos_token == "<end_of_turn>"
    assert model.user_confirmation_required is True
    assert model.license_status == "metadata-gated-manual-confirmation"

    runner = InMemoryRunnerAdapter("ollama")
    runner.pull(model.model_id)
    runner.load(model.model_id)
    provider = LocalModelProvider(runner)
    result = provider.optimize(ModelRequest(prompt="Explain a Python list."))

    assert provider.health().model_id == model.model_id
    assert result.analysis.optimized_prompt
