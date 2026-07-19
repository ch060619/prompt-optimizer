from __future__ import annotations

from prompt_optimizer.services import AppServices

# RC ID: RC-157. Record non-sensitive quality metrics alongside provider metadata.


def test_optimization_metadata_records_quality_without_prompt_content() -> None:
    prompt = "Draft a concise release note for a fixed bug."

    result = AppServices().optimization.optimize(
        original_prompt=prompt,
        prompt=prompt,
        template=None,
        owner_id=None,
    )

    metadata = result.metadata.model_dump()
    assert metadata["quality_score_before"] >= 0
    assert metadata["quality_score_after"] >= 0
    assert metadata["quality_score_delta"] == round(
        metadata["quality_score_after"] - metadata["quality_score_before"],
        2,
    )
    assert "prompt" not in metadata
    assert prompt not in str(metadata)
