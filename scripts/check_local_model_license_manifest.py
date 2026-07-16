#!/usr/bin/env python3
"""RC ID: RC-031. Validate the controlled local-model license manifest."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REGISTER_PATH = Path(__file__).resolve().parents[1] / "docs/research/local-model-license-manifest.yml"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def main() -> int:
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-031 manifest: {exc}", file=sys.stderr)
        return 1
    errors: list[str] = []
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-031":
        errors.append("invalid RC-031 manifest schema")
    if payload.get("weights_downloaded") is not False or payload.get("default_packaging_policy") != "no-model-weights-in-installer":
        errors.append("weights must remain undownloaded and excluded from installer")
    runners = payload.get("runner_sources", [])
    if {runner.get("id") for runner in runners} != {"ollama", "llama-cpp"}:
        errors.append("manifest must contain Ollama and llama.cpp")
    for runner in runners:
        if runner.get("license_spdx") != "MIT" or runner.get("license_status") != "verified-200":
            errors.append(f"runner license not verified: {runner.get('id')}")
        if not SHA_PATTERN.fullmatch(str(runner.get("head_sha"))):
            errors.append(f"runner SHA invalid: {runner.get('id')}")
    models = payload.get("model_sources", [])
    if {model.get("id") for model in models} != {"gemma-3-1b-it", "qwen2.5-coder-1.5b-instruct"}:
        errors.append("manifest must contain Gemma and Qwen2.5-Coder entries")
    for model in models:
        if not SHA_PATTERN.fullmatch(str(model.get("fixed_sha"))):
            errors.append(f"model commit SHA invalid: {model.get('id')}")
        if model.get("packaging") != "prohibited-by-default":
            errors.append(f"model packaging must be prohibited by default: {model.get('id')}")
        for file_info in model.get("file_metadata", []):
            if not HASH_PATTERN.fullmatch(str(file_info.get("sha256"))) or not isinstance(file_info.get("size_bytes"), int):
                errors.append(f"invalid file metadata: {model.get('id')}:{file_info.get('path')}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-031 local-model manifest: 2 runners, 2 models, weights not downloaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
