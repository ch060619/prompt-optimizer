#!/usr/bin/env python3
"""RC ID: RC-240. Run the deterministic offline prompt-quality gate."""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
from typing import Any

from prompt_optimizer.core.language import LanguageProfile
from prompt_optimizer.core.structure import StructuredPrompt
from prompt_optimizer.evaluation import EvaluationService
from prompt_optimizer.services import AppServices

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "evaluation" / "prompts.yml"
REPORT = ROOT / "docs" / "evidence" / "RC-240" / "quality-report.json"
MIN_SCORE_DELTA = 0.0
MIN_SEMANTIC_SIMILARITY = 0.01


def _normalized(text: str) -> str:
    return "".join(text.split()).casefold()


def build_report() -> dict[str, Any]:
    services = AppServices()
    evaluation = EvaluationService(services)
    dataset = evaluation.load_dataset(DATASET)
    rows: list[dict[str, Any]] = []
    groups: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for case in dataset.cases:
        before = services.analyzer.analyze(case.prompt)
        result = services.optimization.optimize(
            original_prompt=case.prompt,
            prompt=case.prompt,
            template=None,
            provider_name="offline",
            save_prompt_history=False,
        )
        optimized = result.analysis.optimized_prompt or ""
        original_structure = StructuredPrompt.parse(case.prompt)
        optimized_structure = StructuredPrompt.parse(optimized)
        original_language = LanguageProfile.detect(original_structure.language_text())
        optimized_language = LanguageProfile.detect(optimized_structure.language_text())
        original_normalized = _normalized(case.prompt)
        similarity = difflib.SequenceMatcher(None, case.prompt, optimized).ratio()
        row = {
            "id": case.id,
            "category": case.category,
            "provider": result.metadata.provider_used,
            "model": result.metadata.model or "rules",
            "score_before": before.score.total_score,
            "score_after": result.analysis.score.total_score,
            "score_delta": round(result.analysis.score.total_score - before.score.total_score, 2),
            "semantic_similarity": round(similarity, 4),
            "semantic_anchor": original_normalized in _normalized(optimized),
            "structure_preserved": original_structure.signature() == optimized_structure.signature(),
            "language_preserved": (
                original_language.translation_requested
                or original_language.primary == "other"
                or (
                    original_language.primary == "mixed"
                    and optimized_language.chinese_letters > 0
                    and optimized_language.latin_letters > 0
                )
                or original_language.primary == optimized_language.primary
            ),
        }
        rows.append(row)
        group = groups.setdefault(
            f"{row['provider']}/{row['model']}",
            {"provider": row["provider"], "model": row["model"], "cases": 0, "score_delta": []},
        )
        group["cases"] += 1
        group["score_delta"].append(row["score_delta"])
        if row["score_delta"] < MIN_SCORE_DELTA:
            failures.append(f"{case.id}: score regression")
        if row["semantic_similarity"] < MIN_SEMANTIC_SIMILARITY or not row["semantic_anchor"]:
            failures.append(f"{case.id}: semantic preservation failed")
        if not row["structure_preserved"]:
            failures.append(f"{case.id}: structure preservation failed")
        if not row["language_preserved"]:
            failures.append(f"{case.id}: language preservation failed")

    for group in groups.values():
        deltas = group.pop("score_delta")
        group["average_score_delta"] = round(sum(deltas) / len(deltas), 2)
    return {
        "schema_version": 1,
        "rc_id": "RC-240",
        "dataset_version": dataset.version,
        "random_seed": dataset.random_seed,
        "thresholds": {
            "minimum_score_delta": MIN_SCORE_DELTA,
            "minimum_semantic_similarity": MIN_SEMANTIC_SIMILARITY,
            "semantic_anchor_required": True,
            "structure_preserved": True,
            "language_preserved": True,
        },
        "blind_review": dataset.blind_review,
        "groups": sorted(groups.values(), key=lambda item: f"{item['provider']}/{item['model']}"),
        "cases": rows,
        "failures": failures,
        "passed": not failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    report = build_report()
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(serialized, encoding="utf-8")
        print(f"Wrote {REPORT.relative_to(ROOT)}")
    elif not REPORT.is_file() or REPORT.read_text(encoding="utf-8") != serialized:
        print("ERROR: RC-240 quality report is stale; run with --write")
        return 1
    if not report["passed"]:
        for failure in report["failures"]:
            print(f"ERROR: {failure}")
        return 1
    print(f"RC-240 quality gate passed: {len(report['cases'])} cases, {len(report['groups'])} provider/model group(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
