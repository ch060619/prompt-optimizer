#!/usr/bin/env python3
"""RC ID: RC-283. Prohibit mislabeling Claude Code proprietary components.

Checks:
    1. No Claude CLI/SDK bundled artifacts in dependency manifests
    2. No Claude Code source map restoration artifacts in source tree
    3. Documentation does not call Claude Code "Rabbit Code open source"
    4. SBOM has zero Claude Code proprietary hits
    5. Optional official Claude integrations mark external terms
    6. Existing denylist (RC-023) covers Claude Code artifacts
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Claude Code proprietary markers that must NOT appear in product source
CLAUDE_PROPRIETARY_MARKERS = [
    "claude-code-sourcemap",
    "claude-code-rev",
    "claude-code-source-code-deobfuscation",
    "@anthropic-ai/claude-code",
    "claude-code/cli",
    "claude-code/sdk",
]

# Documentation markers that would mislabel Claude Code as Rabbit Code
MISLABELING_PATTERNS = [
    "claude code is rabbit code",
    "claude code is open source",
    "claude code is part of rabbit code",
    "rabbit code includes claude code",
    "rabbit code bundles claude code",
]

# Product source paths to scan
PRODUCT_PATHS = ["backend/src", "frontend/src", "scripts", "docs"]
# Exclude evidence/research/legal directories
EXCLUDED_DIRS = {"docs/research", "docs/evidence", "docs/legal", "docs/traceability"}
EXCLUDED_FILES = {
    "scripts/check_rc283_claude_prohibited.py",
    "scripts/check_source_map_denylist.py",
    "scripts/check_proprietary_content_policy.py",
    "scripts/test_source_map_denylist.py",
    "scripts/check_independent_design.py",
    "scripts/check_mit_analysis_source_audit.py",
    "scripts/check_source_map_evidence.py",
    "scripts/check_clean_room_boundary.py",
    "scripts/check_rc291_source_map.py",
    "scripts/check_rc300_310_final.py",
}
# Execution plan legitimately references these terms in task descriptions
EXCLUDED_DOC_FILES = {
    "docs/rabbit-code-310-detailed-execution.md",
}


def scan_source_tree() -> list[tuple[str, str]]:
    """Scan product source for Claude Code proprietary markers."""
    hits: list[tuple[str, str]] = []
    for product_path in PRODUCT_PATHS:
        base = ROOT / product_path
        if not base.is_dir():
            continue
        for file_path in base.rglob("*"):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(ROOT).as_posix()
            # Skip excluded directories
            if any(rel.startswith(excluded) for excluded in EXCLUDED_DIRS):
                continue
            # Skip excluded files
            if rel in EXCLUDED_FILES or rel in EXCLUDED_DOC_FILES:
                continue
            # Skip check scripts that reference these markers for validation
            if "check_rc283" in rel or "check_source_map" in rel or "check_proprietary" in rel:
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for marker in CLAUDE_PROPRIETARY_MARKERS:
                if marker in content:
                    hits.append((rel, marker))
    return hits


def check_dependency_manifests() -> list[str]:
    """Check that Claude CLI/SDK is not a dependency."""
    errors: list[str] = []
    # Check pyproject.toml
    pyproject = ROOT / "backend" / "pyproject.toml"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8")
        for marker in CLAUDE_PROPRIETARY_MARKERS:
            if marker in text:
                errors.append(f"Claude proprietary marker '{marker}' found in pyproject.toml")
    # Check package.json
    package_json = ROOT / "frontend" / "package.json"
    if package_json.is_file():
        text = package_json.read_text(encoding="utf-8")
        for marker in CLAUDE_PROPRIETARY_MARKERS:
            if marker in text:
                errors.append(f"Claude proprietary marker '{marker}' found in package.json")
    # Check package-lock.json
    package_lock = ROOT / "frontend" / "package-lock.json"
    if package_lock.is_file():
        text = package_lock.read_text(encoding="utf-8")
        for marker in CLAUDE_PROPRIETARY_MARKERS:
            if marker in text:
                errors.append(f"Claude proprietary marker '{marker}' found in package-lock.json")
    # Check Cargo.toml
    cargo = ROOT / "apps" / "desktop" / "src-tauri" / "Cargo.toml"
    if cargo.is_file():
        text = cargo.read_text(encoding="utf-8")
        for marker in CLAUDE_PROPRIETARY_MARKERS:
            if marker in text:
                errors.append(f"Claude proprietary marker '{marker}' found in Cargo.toml")
    return errors


def check_documentation_mislabeling() -> list[str]:
    """Check that documentation doesn't mislabel Claude Code as Rabbit Code."""
    errors: list[str] = []
    docs_dir = ROOT / "docs"
    if not docs_dir.is_dir():
        return errors
    for file_path in docs_dir.rglob("*.md"):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(ROOT).as_posix()
        if any(rel.startswith(excluded) for excluded in EXCLUDED_DIRS):
            continue
        try:
            content = file_path.read_text(encoding="utf-8").lower()
        except (OSError, UnicodeDecodeError):
            continue
        for pattern in MISLABELING_PATTERNS:
            if pattern in content:
                errors.append(f"Mislabeling pattern '{pattern}' found in {rel}")
    # Check README
    readme = ROOT / "README.md"
    if readme.is_file():
        content = readme.read_text(encoding="utf-8").lower()
        for pattern in MISLABELING_PATTERNS:
            if pattern in content:
                errors.append(f"Mislabeling pattern '{pattern}' found in README.md")
    return errors


def check_denylist_covers_claude() -> list[str]:
    """Verify the RC-023 denylist covers Claude Code artifacts."""
    errors: list[str] = []
    denylist = ROOT / "docs" / "research" / "source-map-denylist.yml"
    if not denylist.is_file():
        errors.append("source-map-denylist.yml not found")
        return errors
    text = denylist.read_text(encoding="utf-8")
    required_entries = ["claude-code-sourcemap", "claude-code-rev"]
    for entry in required_entries:
        if entry not in text:
            errors.append(f"Denylist missing Claude Code entry: {entry}")
    return errors


def check_external_integration_marking() -> list[str]:
    """Verify Claude Code integration (if any) marks external terms."""
    errors: list[str] = []
    # Check ADR-0013 (Claude Code provider boundary)
    adr = ROOT / "docs" / "adr" / "0013-claude-code-provider-boundary.md"
    if adr.is_file():
        text = adr.read_text(encoding="utf-8")
        if "external" not in text.lower() and "官方" not in text and "official" not in text.lower():
            errors.append("ADR-0013 should mark Claude Code integration as external/official")
    else:
        errors.append("ADR-0013 (Claude Code provider boundary) not found")
    # Check ADR-0004 (Claude Agent SDK rights boundary)
    adr4 = ROOT / "docs" / "adr" / "0004-claude-agent-sdk-rights-boundary.md"
    if not adr4.is_file():
        errors.append("ADR-0004 (Claude Agent SDK rights boundary) not found")
    return errors


def check_sbom_zero_claude() -> list[str]:
    """If SBOM exists, verify zero Claude Code proprietary hits."""
    errors: list[str] = []
    sbom = ROOT / "output" / "supply-chain" / "sbom.json"
    if not sbom.is_file():
        # SBOM not generated yet — skip (not an error)
        return errors
    try:
        data = json.loads(sbom.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        errors.append("SBOM exists but cannot be parsed")
        return errors
    # Check components for Claude proprietary markers
    components = data.get("components", [])
    for comp in components:
        name = str(comp.get("name", "")).lower()
        for marker in CLAUDE_PROPRIETARY_MARKERS:
            if marker in name:
                errors.append(f"Claude proprietary component '{marker}' found in SBOM")
    return errors


def main() -> int:
    all_errors: list[str] = []

    # 1. Scan source tree
    source_hits = scan_source_tree()
    for path, marker in source_hits:
        all_errors.append(f"Proprietary marker '{marker}' found in {path}")

    # 2. Check dependency manifests
    all_errors.extend(check_dependency_manifests())

    # 3. Check documentation mislabeling
    all_errors.extend(check_documentation_mislabeling())

    # 4. Check denylist covers Claude
    all_errors.extend(check_denylist_covers_claude())

    # 5. Check external integration marking
    all_errors.extend(check_external_integration_marking())

    # 6. Check SBOM (if exists)
    all_errors.extend(check_sbom_zero_claude())

    if all_errors:
        print("FAIL: RC-283 Claude Code prohibited components check", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-283 Claude Code prohibited components check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
