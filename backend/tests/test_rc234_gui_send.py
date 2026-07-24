from __future__ import annotations

from pathlib import Path

from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-234. Preserve the adopted prompt when the GUI sends it again.


def test_adopted_optimized_prompt_can_be_sent_again_without_structure_rejection(
    tmp_path: Path,
) -> None:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "rc234.sqlite3"))
    original = "请总结这段文字"
    first = services.optimization.optimize(
        original_prompt=original,
        prompt=original,
        template=None,
        save_prompt_history=False,
    )
    adopted = first.analysis.optimized_prompt
    assert adopted

    events = list(
        services.optimization.stream(
            original_prompt=adopted,
            prompt=adopted,
            template=None,
            save_prompt_history=False,
        )
    )

    assert events[-1].event == "completed"
    assert events[-1].data.analysis.optimized_prompt
