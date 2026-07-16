from __future__ import annotations

# RC ID: RC-048. Export the versioned FastAPI OpenAPI contract.

import argparse
import json
from pathlib import Path

from prompt_optimizer.api.app import app


ROOT = Path(__file__).parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "api" / "openapi-v1.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the versioned Rabbit Code OpenAPI contract.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
