#!/usr/bin/env python3
"""RC ID: RC-123. Validate the Rabbit asset derivative manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "design" / "rabbit-asset-manifest.json"
REQUIRED_VARIANTS = {"full", "avatar", "mark", "empty", "mono", "app-icon"}


def validate_manifest(document: object, require_source: bool = False) -> list[str]:
    if not isinstance(document, dict):
        return ["manifest must be an object"]
    errors: list[str] = []
    source = document.get("source")
    if not isinstance(source, dict) or source.get("status") not in {"pending", "registered"}:
        errors.append("source.status must be pending or registered")
    elif require_source and source.get("status") != "registered":
        errors.append("source is not registered")

    variants = document.get("variants")
    if not isinstance(variants, list):
        return errors + ["variants must be an array"]
    seen: set[str] = set()
    for variant in variants:
        if not isinstance(variant, dict):
            errors.append("each variant must be an object")
            continue
        variant_id = variant.get("id")
        if not isinstance(variant_id, str) or not variant_id:
            errors.append("each variant needs an id")
            continue
        seen.add(variant_id)
        if not isinstance(variant.get("themes"), list) or set(variant["themes"]) != {"light", "dark"}:
            errors.append(f"{variant_id}: themes must contain light and dark")
        if variant_id != "app-icon":
            if not valid_size(variant.get("size_1x")) or not valid_size(variant.get("size_2x")):
                errors.append(f"{variant_id}: size_1x and size_2x are required")
        elif not isinstance(variant.get("sizes"), list) or not variant["sizes"]:
            errors.append("app-icon: sizes are required")
        if not isinstance(variant.get("min_display_px"), int) or variant["min_display_px"] <= 0:
            errors.append(f"{variant_id}: min_display_px must be positive")
        if not isinstance(variant.get("safe_zone"), str) or not variant["safe_zone"].strip():
            errors.append(f"{variant_id}: safe_zone is required")
    missing = REQUIRED_VARIANTS - seen
    errors.extend(f"missing variant: {variant_id}" for variant_id in sorted(missing))
    return errors


def valid_size(value: object) -> bool:
    return isinstance(value, list) and len(value) == 2 and all(isinstance(item, int) and item > 0 for item in value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-source", action="store_true")
    args = parser.parse_args()
    try:
        document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: cannot read manifest: {error}")
        return 1
    errors = validate_manifest(document, require_source=args.require_source)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Rabbit asset manifest is valid ({len(document['variants'])} variants); source status={document['source']['status']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
