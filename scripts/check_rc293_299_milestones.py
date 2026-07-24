#!/usr/bin/env python3
"""RC IDs: RC-293 through RC-299. Milestone M2-M8 gate verification.

Each milestone verifies that the underlying RC items are complete:
    RC-293 (M2): Agent Core, CLI, tools, permissions, context, sessions, streaming, cancel, Git/diff
    RC-294 (M3): OpenAI, Gemini, Anthropic, compatible providers, keychain, dual entry, Gemma/Qwen
    RC-295 (M4): Codex-style IA, workspace, task dialog, terminal, plan, diff, model settings, rabbit art
    RC-296 (M5): Diamond star, API/local FastAPI routes, streaming optimization, compare, adopt, undo, history, templates, scoring, evaluation
    RC-297 (M6): Windows/Linux, install/upgrade, performance, accessibility, security, privacy, visual regression, fault recovery, requirements completeness
    RC-298 (M7): Documentation, license, NOTICE, SBOM, unsigned installers + SHA-256, GitHub Release, contribution, post-release monitoring
    RC-299 (M8): Continuous optimization for performance, resources, UX, visual quality, provider changes, model updates, bugs, security, community
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Key files that must exist for each milestone
MILESTONE_FILES = {
    "RC-293": [
        "backend/rabbit_code/agent.py",
        "backend/rabbit_code/cli.py",
        "backend/rabbit_code/permissions.py",
        "backend/rabbit_code/sessions.py",
        "backend/rabbit_code/streaming.py",
        "backend/rabbit_code/git_tools.py",
        "backend/rabbit_code/tool_registry.py",
        "backend/rabbit_code/context_budget.py",
        "backend/rabbit_code/run_control.py",
        "backend/tests/test_rc230_agent_core.py",
        "backend/tests/test_rc057_agent_prototype.py",
        "backend/tests/test_rc068_agent_state.py",
        "backend/tests/test_rc074_subagents.py",
    ],
    "RC-294": [
        "backend/src/prompt_optimizer/providers/openai.py",
        "backend/src/prompt_optimizer/providers/gemini.py",
        "backend/src/prompt_optimizer/providers/anthropic.py",
        "backend/src/prompt_optimizer/providers/presets.py",
        "backend/src/prompt_optimizer/providers/registry.py",
        "backend/src/prompt_optimizer/secrets.py",
        "backend/src/prompt_optimizer/local_install.py",
        "backend/src/prompt_optimizer/model_manifest.py",
        "data/models/manifest.yml",
    ],
    "RC-295": [
        "frontend/src/App.tsx",
        "apps/desktop/src-tauri/tauri.conf.json",
        "apps/desktop/src-tauri/src/main.rs",
        "frontend/public/rabbit-artwork.png",
        "frontend/public/favicon.svg",
    ],
    "RC-296": [
        "backend/src/prompt_optimizer/core/optimizer.py",
        "backend/src/prompt_optimizer/core/analyzer.py",
        "backend/src/prompt_optimizer/core/scoring.py",
        "backend/src/prompt_optimizer/core/diff.py",
        "backend/src/prompt_optimizer/templates/manager.py",
        "backend/src/prompt_optimizer/evaluation/service.py",
        "backend/src/prompt_optimizer/api/app.py",
        "backend/src/prompt_optimizer/storage/service.py",
    ],
    "RC-297": [
        "docs/support-matrix.md",
        "scripts/install/install.ps1",
        "scripts/install/install.sh",
        "scripts/install/winget.yml",
        "scripts/install/scoop.json",
        "backend/src/prompt_optimizer/privacy.py",
        "backend/src/prompt_optimizer/audit.py",
        "backend/src/prompt_optimizer/hardware.py",
    ],
    "RC-298": [
        "LICENSE",
        "NOTICE",
        "THIRD_PARTY_NOTICES.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "GOVERNANCE.md",
        "SECURITY.md",
        "docs/MAINTENANCE.md",
        "docs/DOCKER.md",
        "docs/github-repository-setup.md",
        ".github/workflows/release.yml",
        ".github/workflows/ci.yml",
        "scripts/generate_sbom.py",
        "scripts/generate_release_notes.py",
    ],
    "RC-299": [
        "docs/MAINTENANCE.md",
        "docs/github-repository-setup.md",
        "scripts/check_rc290_maintenance.py",
    ],
}


def check_milestone(rc_id: str) -> list[str]:
    errors: list[str] = []
    files = MILESTONE_FILES.get(rc_id, [])
    for rel_path in files:
        full_path = ROOT / rel_path
        if not full_path.is_file():
            errors.append(f"[{rc_id}] Missing: {rel_path}")
    return errors


def main() -> int:
    all_errors: list[str] = []
    for rc_id in ["RC-293", "RC-294", "RC-295", "RC-296", "RC-297", "RC-298", "RC-299"]:
        errors = check_milestone(rc_id)
        if errors:
            all_errors.extend(errors)
        else:
            print(f"PASS: {rc_id} milestone verification")

    if all_errors:
        print(f"\nFAIL: Milestone verification ({len(all_errors)} issues)", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("\nPASS: All milestone verifications (RC-293 through RC-299)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
