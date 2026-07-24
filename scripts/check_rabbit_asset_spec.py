#!/usr/bin/env python3
"""RC ID: RC-123. Validate the Rabbit asset derivative manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "design" / "rabbit-asset-manifest.json"
REQUIRED_VARIANTS = {"full", "avatar", "mark", "empty", "mono", "app-icon"}
REQUIRED_OUTPUTS = {
    "desktop-png",
    "desktop-webp",
    "terminal-png",
    "terminal-webp",
    "app-icon-png",
    "app-icon-ico",
}


def validate_manifest(
    document: object,
    require_source: bool = False,
    require_outputs: bool = False,
) -> list[str]:
    if not isinstance(document, dict):
        return ["manifest must be an object"]
    errors: list[str] = []
    source = document.get("source")
    if not isinstance(source, dict) or source.get("status") not in {"pending", "registered"}:
        errors.append("source.status must be pending or registered")
    elif require_source and source.get("status") != "registered":
        errors.append("source is not registered")
    elif source.get("status") == "registered":
        validate_file_record(source, "source", errors)

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
    if require_outputs:
        outputs = document.get("outputs")
        if not isinstance(outputs, list):
            errors.append("outputs must be an array")
        else:
            output_ids: set[str] = set()
            for output in outputs:
                if not isinstance(output, dict):
                    errors.append("each output must be an object")
                    continue
                output_id = output.get("id")
                if not isinstance(output_id, str) or not output_id:
                    errors.append("each output needs an id")
                    continue
                output_ids.add(output_id)
                validate_file_record(output, output_id, errors)
                if output_id == "app-icon-png" and isinstance(output.get("path"), str):
                    validate_png_rgba((ROOT / output["path"]).resolve(), output_id, errors)
                max_bytes = output.get("max_bytes")
                if not isinstance(max_bytes, int) or max_bytes <= 0:
                    errors.append(f"{output_id}: max_bytes must be positive")
                elif isinstance(output.get("path"), str):
                    output_path = (ROOT / output["path"]).resolve()
                    if output_path.is_file() and output_path.stat().st_size > max_bytes:
                        errors.append(f"{output_id}: file exceeds max_bytes")
                if not valid_size(output.get("size")):
                    errors.append(f"{output_id}: size is required")
            errors.extend(
                f"missing output: {output_id}"
                for output_id in sorted(REQUIRED_OUTPUTS - output_ids)
            )
    return errors


def validate_file_record(record: dict[str, object], label: str, errors: list[str]) -> None:
    raw_path = record.get("path")
    expected_hash = record.get("sha256")
    if not isinstance(raw_path, str) or not raw_path:
        errors.append(f"{label}: path is required")
        return
    path = (ROOT / raw_path).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        errors.append(f"{label}: path must stay inside the repository")
        return
    if not path.is_file():
        errors.append(f"{label}: file does not exist")
        return
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        errors.append(f"{label}: sha256 is required")
        return
    observed_hash = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    if observed_hash != expected_hash.upper():
        errors.append(f"{label}: sha256 does not match")


def valid_size(value: object) -> bool:
    return isinstance(value, list) and len(value) == 2 and all(isinstance(item, int) and item > 0 for item in value)


def validate_png_rgba(path: Path, label: str, errors: list[str]) -> None:
    if not path.is_file():
        return
    header = path.read_bytes()[:26]
    if len(header) < 26 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        errors.append(f"{label}: invalid PNG header")
    elif header[25] != 6:
        errors.append(f"{label}: PNG must use RGBA color type for Tauri")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-source", action="store_true")
    parser.add_argument("--require-outputs", action="store_true")
    args = parser.parse_args()
    try:
        document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as parse_error:
        print(f"ERROR: cannot read manifest: {parse_error}")
        return 1
    errors = validate_manifest(
        document,
        require_source=args.require_source,
        require_outputs=args.require_outputs,
    )
    if errors:
        for validation_error in errors:
            print(f"ERROR: {validation_error}")
        return 1
    print(f"Rabbit asset manifest is valid ({len(document['variants'])} variants); source status={document['source']['status']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
