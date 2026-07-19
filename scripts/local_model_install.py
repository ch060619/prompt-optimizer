#!/usr/bin/env python3
"""RC ID: RC-185. CLI JSON wrapper for the shared local install core."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path

from prompt_optimizer.install_policy import (
    InstallPermissionError,
    ensure_user_install_paths,
    user_install_paths,
)
from prompt_optimizer.local_install import LocalInstallCore, LocalInstallError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["start", "download", "pause", "resume", "cancel", "verify", "install", "run", "status"])
    parser.add_argument("--root", type=Path, help="user model root; defaults to the user data directory")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--model-id", default="local-model")
    parser.add_argument("--runner", default="ollama")
    parser.add_argument("--checksum")
    parser.add_argument("--version", default="local-source")
    parser.add_argument("--mirror")
    parser.add_argument("--proxy")
    parser.add_argument("--retries", type=int, default=0)
    parser.add_argument("--backoff-seconds", type=float, default=0.1)
    parser.add_argument("--license-confirmation-version")
    parser.add_argument("--license-url")
    parser.add_argument("--license-summary")
    parser.add_argument("--step-bytes", type=int, default=1024 * 1024)
    parser.add_argument("--accept-license", action="store_true")
    args = parser.parse_args()
    try:
        paths = user_install_paths()
        selected_paths = paths.with_model_root(args.root) if args.root else paths
        ensure_user_install_paths(selected_paths)
        core = LocalInstallCore(selected_paths.model_root)
        if args.command == "start":
            if args.source is None:
                parser.error("start requires --source")
            checksum = args.checksum or sha256(args.source.read_bytes()).hexdigest()
            event = core.start(
                model_id=args.model_id,
                runner=args.runner,
                source=args.source,
                checksum=checksum,
                license_accepted=args.accept_license,
                version=args.version,
                mirror=args.mirror,
                proxy=args.proxy,
                max_retries=args.retries,
                retry_backoff_seconds=args.backoff_seconds,
                license_confirmation_version=args.license_confirmation_version,
                license_url=args.license_url,
                license_summary=args.license_summary,
            )
        elif args.command == "download":
            event = core.download_step(max_bytes=args.step_bytes)
        elif args.command == "pause":
            event = core.pause()
        elif args.command == "resume":
            event = core.resume()
        elif args.command == "cancel":
            event = core.cancel()
        elif args.command == "verify":
            event = core.verify()
        elif args.command == "install":
            event = core.install()
        elif args.command == "run":
            event = core.run()
        else:
            event = {"event": "status", "state": core.state.to_dict() if core.state else None}
    except (InstallPermissionError, LocalInstallError) as exc:
        print(json.dumps({"event": "error", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(event, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
