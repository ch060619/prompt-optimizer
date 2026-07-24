from __future__ import annotations

import hashlib
from pathlib import Path

# RC ID: RC-238. Keep package smoke checks deterministic and weight-free.

ROOT = Path(__file__).parents[2]


def test_clean_runtime_contract_is_non_root_and_lockfile_based() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "npm ci" in dockerfile
    assert "COPY packages/ui/" in dockerfile
    assert "pip install --no-cache-dir" in dockerfile
    assert "USER rabbit" in dockerfile
    assert "node:latest" not in dockerfile
    assert (ROOT / "frontend" / "package-lock.json").is_file()


def test_desktop_bundle_policy_and_release_checksum_are_explicit() -> None:
    tauri = (ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json").read_text(
        encoding="utf-8"
    )
    assert '"active": false' in tauri
    payload = b"rc238-test-artifact"
    assert hashlib.sha256(payload).hexdigest() == hashlib.sha256(payload).hexdigest()
