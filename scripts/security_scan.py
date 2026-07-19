#!/usr/bin/env python3
"""RC ID: RC-211. Run repository security gates that are deterministic in CI."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PRODUCT_PATHS = (
    Path("backend/src"),
    Path("backend/rabbit_code"),
    Path("frontend/src"),
    Path("scripts"),
    Path(".github"),
)
TEXT_SUFFIXES = {".c", ".cpp", ".js", ".json", ".md", ".py", ".rs", ".sh", ".ts", ".tsx", ".toml", ".yml", ".yaml"}
SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("provider-key", re.compile(r"\b(?:sk-(?:proj-)?|sk-ant-|AIza|xai-|ghp_|github_pat_|hf_|r8_)[A-Za-z0-9_-]{20,}\b")),
    ("secret-assignment", re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*['\"][^'\"\n]{16,}['\"]")),
)
IGNORED_PARTS = frozenset({".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__", "dist", "node_modules", ".venv"})


def _iter_product_files(root: Path):
    for relative in PRODUCT_PATHS:
        path = root / relative
        if path.is_file():
            yield path
            continue
        if not path.is_dir():
            continue
        for candidate in path.rglob("*"):
            if candidate.is_file() and candidate.suffix.lower() in TEXT_SUFFIXES:
                if not any(part in IGNORED_PARTS for part in candidate.relative_to(root).parts):
                    yield candidate


def find_secret_hits(root: Path) -> tuple[tuple[str, int, str], ...]:
    hits: list[tuple[str, int, str]] = []
    for path in _iter_product_files(root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(lines, start=1):
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    hits.append((path.relative_to(root).as_posix(), line_number, name))
                    break
    return tuple(hits)


def validate_dockerfile(path: Path) -> tuple[str, ...]:
    if not path.is_file():
        return ()
    lines = path.read_text(encoding="utf-8").splitlines()
    errors: list[str] = []
    if not any(line.strip().upper().startswith("USER ") for line in lines):
        errors.append("Dockerfile must run the final image as a non-root USER")
    if any(re.search(r"\bFROM\s+[^\s]+:latest\b", line, re.IGNORECASE) for line in lines):
        errors.append("Dockerfile must not use a latest base image")
    if any(line.strip().upper().startswith("ADD ") for line in lines):
        errors.append("Dockerfile must use COPY instead of ADD")
    if any(re.search(r"\bnpm\s+install\b", line) and "npm ci" not in line for line in lines):
        errors.append("Dockerfile must use npm ci with the lockfile")
    if any(re.search(r"\b(?:API_KEY|SECRET|TOKEN|PASSWORD)\b\s*=", line, re.IGNORECASE) for line in lines):
        errors.append("Dockerfile must not bake credentials into ENV or ARG")
    return tuple(errors)


def _version_from_requirement(value: str) -> str:
    match = re.search(r"\d+(?:\.\d+){1,2}", value)
    return match.group(0) if match else "declared"


def build_sbom(root: Path) -> dict[str, Any]:
    pyproject = tomllib.loads((root / "backend/pyproject.toml").read_text(encoding="utf-8"))
    components: dict[tuple[str, str, str], dict[str, str]] = {}
    for requirement in pyproject["project"]["dependencies"]:
        name = re.split(r"[<>=!~;\[]", requirement, maxsplit=1)[0].strip()
        version = _version_from_requirement(requirement)
        purl = f"pkg:pypi/{name.casefold()}@{version}"
        components[("pypi", name, version)] = {
            "bom-ref": purl,
            "name": name,
            "purl": purl,
            "scope": "required",
            "type": "library",
            "version": version,
        }

    lock = json.loads((root / "frontend/package-lock.json").read_text(encoding="utf-8"))
    for location, package in lock.get("packages", {}).items():
        if not location.startswith("node_modules/") or not isinstance(package, dict):
            continue
        version = package.get("version")
        if not isinstance(version, str):
            continue
        name = location.removeprefix("node_modules/")
        purl = f"pkg:npm/{name}@{version}"
        components[("npm", name, version)] = {
            "bom-ref": purl,
            "name": name,
            "purl": purl,
            "scope": "optional" if package.get("optional") else "required",
            "type": "library",
            "version": version,
        }
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {"component": {"name": "rabbit-code", "version": "3.0.0", "type": "application"}},
        "components": [components[key] for key in sorted(components)],
    }


def validate_security_docs(root: Path) -> tuple[str, ...]:
    required = {
        root / "SECURITY.md": ("Security Advisory", "72 hours", "key rotation"),
        root / "docs/security/threat-model.md": ("Data Flow", "STRIDE", "T1", "T2", "T3", "T4", "T5", "T6"),
    }
    errors: list[str] = []
    for path, markers in required.items():
        if not path.is_file():
            errors.append(f"missing security document: {path.relative_to(root).as_posix()}")
            continue
        content = path.read_text(encoding="utf-8").casefold()
        errors.extend(
            f"{path.relative_to(root).as_posix()} missing marker: {marker}"
            for marker in markers
            if marker.casefold() not in content
        )
    return tuple(errors)


def check_repository(root: Path) -> tuple[str, ...]:
    errors = list(validate_security_docs(root))
    errors.extend(
        f"secret pattern {name} at {path}:{line}"
        for path, line, name in find_secret_hits(root)
    )
    errors.extend(validate_dockerfile(root / "Dockerfile"))
    sbom_path = root / "docs/security/sbom.json"
    if not sbom_path.is_file():
        errors.append("missing generated SBOM: docs/security/sbom.json")
    else:
        expected = json.dumps(build_sbom(root), ensure_ascii=False, indent=2) + "\n"
        if sbom_path.read_text(encoding="utf-8") != expected:
            errors.append("SBOM is stale; run security_scan.py --write")
    return tuple(errors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true", help="write the deterministic SBOM")
    action.add_argument("--check", action="store_true", help="run all repository security gates")
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.write:
        path = root / "docs/security/sbom.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(build_sbom(root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path.relative_to(root).as_posix()}")
        return 0
    errors = check_repository(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("RC-211 security baseline passed: threat model, secret scan, Dockerfile, and SBOM are current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
