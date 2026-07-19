from __future__ import annotations

from prompt_optimizer.providers import ProviderRegistry
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-195. Verify selected local model identity reaches metadata and history.


def test_session_model_selection_is_recorded_for_each_request_and_version(tmp_path) -> None:
    services = AppServices(
        providers=ProviderRegistry(),
        versions=VersionService(StorageService(tmp_path / "rc195.sqlite3")),
    )

    gemma = services.optimization.optimize(
        original_prompt="Gemma turn",
        prompt="Gemma turn",
        template=None,
        provider_name="offline",
        model="gemma-3-1b-it",
    )
    qwen = services.optimization.optimize(
        original_prompt="Qwen turn",
        prompt="Qwen turn",
        template=None,
        provider_name="offline",
        model="qwen2.5-coder-1.5b-instruct",
    )

    assert gemma.metadata.model == "gemma-3-1b-it"
    assert qwen.metadata.model == "qwen2.5-coder-1.5b-instruct"
    assert gemma.metadata.selection_scope == "session"
    assert qwen.metadata.selection_scope == "session"
    history = services.versions.list()
    assert [item.model for item in history[:2]] == [
        "qwen2.5-coder-1.5b-instruct",
        "gemma-3-1b-it",
    ]
