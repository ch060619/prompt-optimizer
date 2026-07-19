#!/usr/bin/env python3
"""RC ID: RC-192. Deny model weight files from source and package trees."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

WEIGHT_SUFFIXES = frozenset(
    {
        ".bin",
        ".ckpt",
        ".ggml",
        ".gguf",
        ".model",
        ".onnx",
        ".pt",
        ".pth",
        ".safetensors",
    }
)
IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".runtime",
        ".venv",
        "dist",
        "node_modules",
    }
)


def find_forbidden_weights(root: Path) -> tuple[Path, ...]:
    matches: list[Path] = []
    for current, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in IGNORED_DIRECTORIES]
        current_path = Path(current)
        for name in files:
            if Path(name).suffix.lower() in WEIGHT_SUFFIXES:
                matches.append((current_path / name).relative_to(root))
    return tuple(sorted(matches))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    matches = find_forbidden_weights(args.root)
    if matches:
        for path in matches:
            print(f"Forbidden model weight: {path}")
        return 1
    print("RC-192 distribution policy passed: no model weight files found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
