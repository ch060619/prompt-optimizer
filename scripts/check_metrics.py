#!/usr/bin/env python3
"""RC-219: validate that the local metrics report has no content fields."""

from __future__ import annotations

from prompt_optimizer.metrics import LocalMetricsAggregator


def main() -> int:
    snapshot = LocalMetricsAggregator().snapshot()
    payload = snapshot.model_dump_json().lower()
    forbidden = ("prompt", "source", "path", "secret", "token_value")
    if any(f'"{field}"' in payload for field in forbidden):
        raise SystemExit("metrics snapshot contains a forbidden content field")
    if snapshot.schema_version != "rc219-v1":
        raise SystemExit("unexpected metrics schema version")
    print("Local metrics schema and content boundary are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
