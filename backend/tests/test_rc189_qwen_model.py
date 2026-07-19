from __future__ import annotations

from pathlib import Path

from prompt_optimizer.model_manifest import load_manifest, qwen_coder_model
from prompt_optimizer.providers.base import ModelRequest
from prompt_optimizer.providers.local import LocalModelProvider
from prompt_optimizer.providers.runners import InMemoryRunnerAdapter

# RC ID: RC-189. Verify the controlled Qwen2.5-Coder family and generation smoke path.

MANIFEST = Path(__file__).parents[2] / "data/models/manifest.yml"


def test_qwen_coder_model_id_family_and_generation_smoke() -> None:
    model = qwen_coder_model(load_manifest(MANIFEST))
    runner = InMemoryRunnerAdapter("ollama")
    runner.pull(model.model_id)
    runner.load(model.model_id)
    provider = LocalModelProvider(runner)

    assert provider.health().model_id == "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    result = provider.optimize(ModelRequest(prompt="Write a small Python function."))
    assert result.analysis.optimized_prompt
    assert provider.model == model.model_id
