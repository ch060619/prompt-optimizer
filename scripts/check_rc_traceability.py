#!/usr/bin/env python3
"""RC ID: RC-043. Generate and validate the requirement traceability index."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

REQUIREMENT_PATTERN = re.compile(
    r"^- \[[ x]\] \*\*(RC-\d{3})\*\* (.+)$",
    re.MULTILINE,
)
REFERENCE_PATTERN = re.compile(r"\bRC-\d{3}\b")
REFERENCE_FIELD_PATTERN = re.compile(r"\bRC IDs?:\s*([^\r\n]+)", re.IGNORECASE)
PLAN_PATH = Path("docs/rabbit-code-310-detailed-execution.md")
INDEX_PATH = Path("docs/traceability/rc-index.md")

REQUIRED_TEMPLATES = (
    Path("docs/templates/adr-template.md"),
    Path(".github/ISSUE_TEMPLATE/rabbit-code.yml"),
    Path(".github/pull_request_template.md"),
    Path("docs/templates/test-case-template.md"),
    Path("docs/templates/document-template.md"),
    Path("docs/templates/release-note-template.md"),
)

CODE_ROOTS = (
    Path("backend/src"),
    Path("backend/tests"),
    Path("frontend/src"),
    Path("frontend/tests"),
    Path("scripts"),
)
CODE_SUFFIXES = {".c", ".cc", ".cpp", ".go", ".js", ".jsx", ".py", ".rs", ".ts", ".tsx"}
TEXT_SUFFIXES = CODE_SUFFIXES | {".json", ".md", ".toml", ".yaml", ".yml"}
IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".runtime",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
}
EXCLUDED_REPORT_INPUTS = {PLAN_PATH.as_posix(), INDEX_PATH.as_posix()}


def load_requirements(plan_path: Path) -> dict[str, str]:
    """Load the canonical checklist, rejecting duplicate or missing RC IDs."""
    content = plan_path.read_text(encoding="utf-8")
    pairs = REQUIREMENT_PATTERN.findall(content)
    requirements = dict(pairs)
    if len(requirements) != len(pairs):
        raise ValueError("The master plan contains duplicate RC IDs")

    expected = [f"RC-{number:03d}" for number in range(1, 311)]
    if list(requirements) != expected:
        raise ValueError("The master plan must contain RC-001 through RC-310 in order")
    return requirements


def validate_templates(repository_root: Path) -> list[str]:
    """Return template contract violations without mutating the repository."""
    errors: list[str] = []
    for relative_path in REQUIRED_TEMPLATES:
        path = repository_root / relative_path
        if not path.is_file():
            errors.append(f"missing template: {relative_path.as_posix()}")
            continue
        content = path.read_text(encoding="utf-8")
        if "RC ID" not in content or "RC-xxx" not in content:
            errors.append(f"missing RC ID field: {relative_path.as_posix()}")
    return errors


def _is_ignored(relative_path: Path) -> bool:
    return any(part in IGNORED_PARTS for part in relative_path.parts)


def _is_code_file(relative_path: Path) -> bool:
    return relative_path.suffix.lower() in CODE_SUFFIXES and any(
        relative_path.is_relative_to(root) for root in CODE_ROOTS
    )


def _iter_text_files(repository_root: Path) -> Iterable[tuple[Path, Path]]:
    for path in repository_root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(repository_root)
        relative_posix = relative_path.as_posix()
        if _is_ignored(relative_path) or relative_posix in EXCLUDED_REPORT_INPUTS:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        yield path, relative_path


def scan_references(
    repository_root: Path,
    requirements: Mapping[str, str],
) -> tuple[dict[str, list[str]], list[str]]:
    """Collect RC references and source files that have no valid RC marker."""
    references = {rc_id: [] for rc_id in requirements}
    orphan_code: list[str] = []

    for path, relative_path in _iter_text_files(repository_root):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        declared = {
            rc_id
            for field in REFERENCE_FIELD_PATTERN.findall(content)
            for rc_id in REFERENCE_PATTERN.findall(field.upper())
        }
        found = sorted(declared & requirements.keys())
        relative_posix = relative_path.as_posix()
        for rc_id in found:
            references[rc_id].append(relative_posix)
        if _is_code_file(relative_path) and not found:
            orphan_code.append(relative_posix)

    for paths in references.values():
        paths.sort()
    return references, sorted(orphan_code)


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _link(path: str) -> str:
    return f"[{path}](../../{path})"


def render_markdown(
    requirements: Mapping[str, str],
    references: Mapping[str, list[str]],
    orphan_code: list[str],
) -> str:
    """Render a deterministic human-readable reverse index."""
    linked_count = sum(bool(references[rc_id]) for rc_id in requirements)
    lines = [
        "# Rabbit Code RC 反向追踪索引",
        "",
        "<!-- Generated by scripts/check_rc_traceability.py; do not edit manually. -->",
        "",
        f"- 需求总数：{len(requirements)}",
        f"- 已有关联证据：{linked_count}",
        f"- RED 孤立需求：{len(requirements) - linked_count}",
        f"- RED 孤立代码文件：{len(orphan_code)}",
        "",
        "状态说明：`GREEN` 表示仓库中至少有一处计划外 RC 引用；`RED` 表示尚无关联证据。",
        "",
        "## 需求到证据",
        "",
        "| RC ID | 状态 | 证据 | 需求摘要 |",
        "| --- | --- | --- | --- |",
    ]
    for rc_id, description in requirements.items():
        paths = references[rc_id]
        status = "GREEN" if paths else "RED"
        evidence = ", ".join(_link(path) for path in paths) if paths else "无"
        lines.append(f"| {rc_id} | {status} | {evidence} | {_escape_cell(description)} |")

    lines.extend(
        [
            "",
            "## 孤立代码",
            "",
            "下列代码文件没有有效 RC 引用；它们必须在对应迁移/维护 RC 中关联或明确处置。",
            "",
            "| 状态 | 文件 |",
            "| --- | --- |",
        ]
    )
    if orphan_code:
        lines.extend(f"| RED | {_link(path)} |" for path in orphan_code)
    else:
        lines.append("| GREEN | 无 |")
    return "\n".join(lines) + "\n"


def _query(
    rc_id: str,
    requirements: Mapping[str, str],
    references: Mapping[str, list[str]],
) -> int:
    normalized = rc_id.upper()
    if normalized not in requirements:
        print(f"Unknown RC ID: {normalized}", file=sys.stderr)
        return 2
    payload = {
        "rc_id": normalized,
        "status": "GREEN" if references[normalized] else "RED",
        "requirement": requirements[normalized],
        "evidence": references[normalized],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _check(repository_root: Path, expected_report: str) -> int:
    errors = validate_templates(repository_root)
    index_path = repository_root / INDEX_PATH
    if not index_path.is_file():
        errors.append(f"missing reverse index: {INDEX_PATH.as_posix()}")
    elif index_path.read_text(encoding="utf-8") != expected_report:
        errors.append("reverse index is stale; run with --write")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("RC traceability templates and reverse index are current.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true", help="write the reverse index")
    action.add_argument("--check", action="store_true", help="validate templates and index")
    action.add_argument("--rc", metavar="RC-XXX", help="query one RC ID")
    args = parser.parse_args(argv)

    repository_root = Path(__file__).resolve().parents[1]
    requirements = load_requirements(repository_root / PLAN_PATH)
    references, orphan_code = scan_references(repository_root, requirements)
    report = render_markdown(requirements, references, orphan_code)

    if args.rc:
        return _query(args.rc, requirements, references)
    if args.write:
        index_path = repository_root / INDEX_PATH
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(report, encoding="utf-8")
        print(f"Wrote {INDEX_PATH.as_posix()}")
        return 0
    return _check(repository_root, report)


if __name__ == "__main__":
    raise SystemExit(main())
