#!/usr/bin/env python3
"""RC-271: check local documentation links, assets, commands, and marked smoke blocks."""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = (
    ROOT / "README.md",
    ROOT / "README.en.md",
    ROOT / "SECURITY.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "CODE_OF_CONDUCT.md",
    ROOT / "ROADMAP.md",
    ROOT / "CHANGELOG.md",
    ROOT / ".github" / "pull_request_template.md",
    ROOT / "docs" / "architecture" / "rabbit-code.md",
    ROOT / "docs" / "architecture" / "agents-navigation.md",
    ROOT / "docs" / "architecture.md",
    ROOT / "docs" / "contribution.md",
    ROOT / "docs" / "community" / "discussions.md",
    ROOT / "docs" / "providers" / "provider-integration.md",
    ROOT / "docs" / "providers" / "local-models.md",
    ROOT / "docs" / "user-guide.md",
    ROOT / "docs" / "development-guide.md",
    ROOT / "docs" / "security" / "privacy-and-data.md",
    ROOT / "docs" / "extensions" / "README.md",
    ROOT / "docs" / "support-matrix.md",
    ROOT / "docs" / "reports" / "grok-build-analysis.md",
    ROOT / "docs" / "reports" / "project-cleanup.md",
    ROOT / "docs" / "reports" / "rc230-271-remediation.md",
    *(ROOT / "docs" / "evidence" / f"RC-{number:03d}" / "README.md" for number in range(262, 272)),
)
REQUIRED_ASSETS = (ROOT / "桌面端参考图.png", ROOT / "终端参考图.png")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FENCE_RE = re.compile(r"^(`{3,}|~{3,})([^\r\n]*)\r?$", re.MULTILINE)
MARKER = "<!-- docs-check:run -->"


def _local_target(raw: str) -> Path | None:
    target = raw.strip().split("#", 1)[0].strip()
    if not target or target.startswith(("http://", "https://", "mailto:", "data:")):
        return None
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return Path(target)


def check_links() -> list[str]:
    errors: list[str] = []
    for document in DOCS:
        if not document.is_file():
            errors.append(f"missing documentation file: {document.relative_to(ROOT)}")
            continue
        text = document.read_text(encoding="utf-8")
        for raw in LINK_RE.findall(text):
            target = _local_target(raw)
            if target is None:
                continue
            resolved = (document.parent / target).resolve()
            if not resolved.is_file() and not resolved.is_dir():
                errors.append(f"{document.relative_to(ROOT)}: missing link target {raw}")
    for asset in REQUIRED_ASSETS:
        if not asset.is_file():
            errors.append(f"missing required screenshot asset: {asset.relative_to(ROOT)}")
    return errors


def _fenced_blocks(text: str) -> list[tuple[str, str, bool]]:
    blocks: list[tuple[str, str, bool]] = []
    matches = list(FENCE_RE.finditer(text))
    for index, opening in enumerate(matches):
        closing = next(
            (candidate for candidate in matches[index + 1 :] if candidate.group(1)[0] == opening.group(1)[0]),
            None,
        )
        if closing is None:
            continue
        language = opening.group(2).strip().lower()
        body = text[opening.end() : closing.start()]
        marked = text[max(0, opening.start() - len(MARKER) - 2) : opening.start()].strip().endswith(MARKER)
        blocks.append((language, body, marked))
    return blocks


def check_command_references() -> list[str]:
    errors: list[str] = []
    command_pattern = re.compile(r"(?:python|py|bash|sh|npm|cargo|rabbit|prompt-opt)\s+[^\s`]+")
    for document in DOCS:
        if not document.is_file():
            continue
        text = document.read_text(encoding="utf-8")
        for language, body, _marked in _fenced_blocks(text):
            if language not in {"bash", "sh", "shell", "powershell", "pwsh", "python", "console", "text"}:
                continue
            for line in body.splitlines():
                line = line.strip().lstrip("$>")
                if not line or line.startswith(("#", "::", "REM ")):
                    continue
                match = command_pattern.search(line)
                if match is None:
                    continue
                script_match = re.search(r"(?:python|py)\s+(scripts[\\/]\S+?\.py)", line)
                if script_match:
                    relative = Path(script_match.group(1).replace("\\", os.sep))
                    if not (ROOT / relative).is_file():
                        errors.append(f"{document.relative_to(ROOT)}: missing command script {relative}")
    return errors


def check_installation_flow() -> list[str]:
    required = {
        ROOT / "README.md": (
            "python -m venv .venv",
            "python -m pip install -e \"backend[dev]\"",
            "npm --prefix frontend install",
            "npm --prefix frontend run build",
            "rabbit serve",
        ),
        ROOT / "README.en.md": (
            "python -m venv .venv",
            "python -m pip install -e \"backend[dev]\"",
            "npm --prefix frontend install",
            "npm --prefix frontend run build",
            "rabbit serve",
        ),
        ROOT / "docs" / "development-guide.md": (
            "python scripts/workspace.py verify",
            "docker build -t rabbit-code:local .",
            "cargo check --manifest-path apps/desktop/src-tauri/Cargo.toml",
        ),
        ROOT / "docs" / "providers" / "local-models.md": (
            "scripts\\install-local-model.ps1",
            "scripts/local_model_install.py",
            "--checksum",
            "--accept-license",
        ),
    }
    errors: list[str] = []
    for document, markers in required.items():
        text = document.read_text(encoding="utf-8") if document.is_file() else ""
        for marker in markers:
            if marker not in text:
                errors.append(f"{document.relative_to(ROOT)}: missing installation marker {marker}")
    return errors


def check_performance_references() -> list[str]:
    metric_with_number = re.compile(
        r"\b(?:qps|throughput|coverage|p(?:50|95|99)|latency)\b[^\r\n]{0,60}\d",
        re.IGNORECASE,
    )
    managed = (
        ROOT / "README.md",
        ROOT / "README.en.md",
        ROOT / "docs" / "user-guide.md",
        ROOT / "docs" / "development-guide.md",
    )
    errors: list[str] = []
    for document in managed:
        if not document.is_file():
            continue
        for line_number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), 1):
            if metric_with_number.search(line):
                errors.append(
                    f"{document.relative_to(ROOT)}:{line_number}: performance metrics must come from baseline JSON"
                )
    if not (ROOT / "docs" / "performance" / "baseline.json").is_file():
        errors.append("missing docs/performance/baseline.json for performance references")
    return errors


def _marked_commands() -> list[tuple[Path, str, str]]:
    commands: list[tuple[Path, str, str]] = []
    for document in DOCS:
        if not document.is_file():
            continue
        for language, body, marked in _fenced_blocks(document.read_text(encoding="utf-8")):
            if not marked or language not in {"python", "console"}:
                continue
            for line in body.splitlines():
                command = line.strip().lstrip("$>")
                if command and not command.startswith("#"):
                    commands.append((document, language, command))
    return commands


def run_marked_commands() -> list[str]:
    errors: list[str] = []
    for document, language, command in _marked_commands():
        try:
            argv = shlex.split(command, posix=os.name != "nt")
            if not argv:
                continue
            if argv[0] in {"python", "py"}:
                argv[0] = sys.executable
            environment = os.environ.copy()
            environment["PYTHONPATH"] = os.pathsep.join(
                str(ROOT / part) for part in ("backend/src", "backend", "packages/protocol")
            )
            result = subprocess.run(
                argv,
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            errors.append(f"{document.relative_to(ROOT)}: could not run {command!r}: {exc}")
            continue
        if result.returncode != 0:
            output = (result.stdout + result.stderr).strip().replace("\n", " ")[-240:]
            errors.append(f"{document.relative_to(ROOT)}: {command!r} exited {result.returncode}: {output}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="run only explicitly marked safe smoke blocks")
    args = parser.parse_args()
    errors = (
        check_links()
        + check_command_references()
        + check_installation_flow()
        + check_performance_references()
    )
    if args.run:
        errors.extend(run_marked_commands())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Documentation checks passed for {len(DOCS)} documents.")
    if args.run:
        print(f"Ran {len(_marked_commands())} marked smoke command(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
