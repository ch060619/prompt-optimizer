#!/usr/bin/env python3
"""RC ID: RC-188. Validate the controlled model manifest and safe recommendation rules."""

from __future__ import annotations

from pathlib import Path

from prompt_optimizer.model_manifest import HardwareCapacity, load_manifest, recommend_models


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/models/manifest.yml"


def main() -> int:
    models = load_manifest(MANIFEST)
    recommendations = recommend_models(
        models,
        HardwareCapacity(ram_bytes=8 * 1024**3, disk_free_bytes=16 * 1024**3, vram_bytes=4 * 1024**3),
    )
    print(f"Validated RC-188 model manifest: {len(models)} models, {sum(item.recommended for item in recommendations)} recommended.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
