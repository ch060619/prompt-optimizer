#!/usr/bin/env python3
"""RC ID: RC-200. Import a validated offline local-model package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from prompt_optimizer.install_policy import (
    InstallPermissionError,
    ensure_user_install_paths,
    user_install_paths,
)
from prompt_optimizer.offline_import import OfflineImportError, OfflineModelImporter


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--target-root", type=Path)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--runner", default="ollama")
    parser.add_argument("--accept-license", action="store_true")
    parser.add_argument("--license-confirmation-version", required=True)
    args = parser.parse_args()
    try:
        paths = user_install_paths()
        selected = paths.with_model_root(args.target_root) if args.target_root else paths
        ensure_user_install_paths(selected)
        result = OfflineModelImporter(
            selected.model_root,
            runner_name=args.runner,
            resource_probe=lambda: 1,
        ).import_package(
            args.package,
            model_id=args.model_id,
            license_accepted=args.accept_license,
            license_confirmation_version=args.license_confirmation_version,
        )
    except (InstallPermissionError, OfflineImportError) as exc:
        print(json.dumps({"event": "error", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if result.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
