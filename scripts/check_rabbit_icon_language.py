#!/usr/bin/env python3
"""RC ID: RC-131. Keep Sparkles and star-shaped icons within their semantic owners."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SOURCE = ROOT / "frontend" / "src"
OPTIMIZATION_OWNER = Path("frontend/src/App.tsx")


def source_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for path in sorted(FRONTEND_SOURCE.rglob("*.tsx")):
        files.append((path.relative_to(ROOT), path.read_text(encoding="utf-8")))
    return files


def validate(files: list[tuple[Path, str]]) -> list[str]:
    errors: list[str] = []
    sparkles_files = [path for path, content in files if "Sparkles" in content]
    if sparkles_files != [OPTIMIZATION_OWNER]:
        rendered = ", ".join(path.as_posix() for path in sparkles_files) or "none"
        errors.append(f"Sparkles must be owned only by {OPTIMIZATION_OWNER.as_posix()} (found: {rendered})")

    for path, content in files:
        if "<Star" in content or ", Star," in content:
            errors.append(f"unscoped Star icon remains in {path.as_posix()}; use Heart or Pin for non-optimization actions")

    by_path = {path: content for path, content in files}
    if "<RabbitMark" not in by_path.get(Path("frontend/src/App.tsx"), ""):
        errors.append("workspace brand must use RabbitMark")
    if "Cloud" not in by_path.get(Path("frontend/src/onboarding.tsx"), ""):
        errors.append("API onboarding choice must use Cloud")
    return errors


def main() -> int:
    errors = validate(source_files())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Rabbit icon language is valid: Sparkles is reserved for prompt optimization and no unscoped Star remains.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
