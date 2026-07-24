"""RC ID: RC-276. Secure update check, rollback, and version compatibility.

Provides update checking via HTTPS with hash verification, staged rollout
support, rollback capability, and version compatibility hints.
"""

from __future__ import annotations

import hashlib
import json
import platform
import re
import urllib.request
from dataclasses import dataclass, field
from typing import Literal

__all__ = [
    "UpdateInfo",
    "UpdateChecker",
    "RollbackManager",
    "VersionCompatibility",
]

GITHUB_API = "https://api.github.com/repos/rabbit-code/rabbit-code/releases/latest"
UPDATE_MANIFEST_URL = "https://rabbit-code.dev/updates/manifest.json"

RolloutChannel = Literal["stable", "beta", "nightly"]


@dataclass
class UpdateInfo:
    """Information about an available update."""

    current_version: str
    latest_version: str
    download_url: str
    sha256: str
    release_notes: str
    channel: RolloutChannel
    rollout_percentage: int = 100
    min_required_version: str = ""
    breaking_changes: list[str] = field(default_factory=list)

    @property
    def update_available(self) -> bool:
        return _compare_versions(self.latest_version, self.current_version) > 0

    @property
    def is_breaking(self) -> bool:
        return bool(self.breaking_changes)


@dataclass
class VersionCompatibility:
    """Version compatibility assessment."""

    current: str
    target: str
    min_required: str
    is_compatible: bool
    warnings: list[str] = field(default_factory=list)

    def format_hints(self) -> str:
        if self.is_compatible and not self.warnings:
            return f"v{self.current} → v{self.target}: compatible"
        lines = [f"v{self.current} → v{self.target}: {'compatible' if self.is_compatible else 'incompatible'}"]
        for w in self.warnings:
            lines.append(f"  - {w}")
        return "\n".join(lines)


class UpdateChecker:
    """Checks for updates via HTTPS with hash verification."""

    def __init__(self, current_version: str, channel: RolloutChannel = "stable") -> None:
        self.current_version = current_version
        self.channel = channel

    def check(self) -> UpdateInfo | None:
        """Check for available updates. Returns None if up-to-date or check fails."""
        try:
            manifest = self._fetch_manifest()
        except Exception:
            return None

        channel_info = manifest.get("channels", {}).get(self.channel, {})
        if not channel_info:
            return None

        latest = channel_info.get("version", "")
        if not latest or _compare_versions(latest, self.current_version) <= 0:
            return None

        platform_key = _platform_key()
        download = channel_info.get("downloads", {}).get(platform_key, {})
        if not download:
            return None

        breaking = channel_info.get("breaking_changes", [])
        min_required = channel_info.get("min_required_version", "")

        return UpdateInfo(
            current_version=self.current_version,
            latest_version=latest,
            download_url=download.get("url", ""),
            sha256=download.get("sha256", ""),
            release_notes=channel_info.get("release_notes", ""),
            channel=self.channel,
            rollout_percentage=channel_info.get("rollout_percentage", 100),
            min_required_version=min_required,
            breaking_changes=breaking if isinstance(breaking, list) else [],
        )

    def verify_download(self, data: bytes, expected_sha256: str) -> bool:
        """Verify downloaded data matches expected SHA-256 hash."""
        actual = hashlib.sha256(data).hexdigest()
        return actual.lower() == expected_sha256.lower()

    def should_offer_update(self, update: UpdateInfo, user_rollout_id: int = 0) -> bool:
        """Determine if update should be offered based on staged rollout."""
        if update.rollout_percentage >= 100:
            return True
        return (user_rollout_id % 100) < update.rollout_percentage

    def _fetch_manifest(self) -> dict[str, object]:
        """Fetch update manifest via HTTPS."""
        req = urllib.request.Request(
            UPDATE_MANIFEST_URL,
            headers={"User-Agent": f"rabbit-code/{self.current_version}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))


class RollbackManager:
    """Manages version rollback for the CLI application."""

    def __init__(self, install_dir: str) -> None:
        self.install_dir = install_dir

    def backup_current(self, version: str) -> str:
        """Backup current version before update. Returns backup path."""
        import shutil
        from pathlib import Path

        backup_dir = Path(self.install_dir) / ".rollback" / version
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        current = Path(self.install_dir)
        for item in current.iterdir():
            if item.name == ".rollback":
                continue
            if item.is_dir():
                shutil.copytree(item, backup_dir / item.name)
            else:
                shutil.copy2(item, backup_dir / item.name)
        return str(backup_dir)

    def list_backups(self) -> list[str]:
        """List available rollback versions."""
        from pathlib import Path

        rollback_dir = Path(self.install_dir) / ".rollback"
        if not rollback_dir.is_dir():
            return []
        return sorted(
            [d.name for d in rollback_dir.iterdir() if d.is_dir()],
            reverse=True,
        )

    def rollback_to(self, version: str) -> bool:
        """Rollback to a previously backed up version."""
        import shutil
        from pathlib import Path

        backup_dir = Path(self.install_dir) / ".rollback" / version
        if not backup_dir.is_dir():
            return False

        install = Path(self.install_dir)
        # Remove current files (except .rollback)
        for item in install.iterdir():
            if item.name == ".rollback":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        # Restore from backup
        for item in backup_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, install / item.name)
            else:
                shutil.copy2(item, install / item.name)
        return True


def check_version_compatibility(
    current: str,
    target: str,
    min_required: str = "",
) -> VersionCompatibility:
    """Check if upgrading from current to target version is compatible."""
    warnings: list[str] = []

    if min_required and _compare_versions(current, min_required) < 0:
        return VersionCompatibility(
            current=current,
            target=target,
            min_required=min_required,
            is_compatible=False,
            warnings=[f"v{target} requires minimum v{min_required}, current is v{current}"],
        )

    # Check for major version jump
    cur_major = _parse_major(current)
    tgt_major = _parse_major(target)
    if tgt_major > cur_major + 1:
        warnings.append(f"Major version jump ({cur_major} → {tgt_major}), review release notes carefully")

    return VersionCompatibility(
        current=current,
        target=target,
        min_required=min_required,
        is_compatible=True,
        warnings=warnings,
    )


def _compare_versions(a: str, b: str) -> int:
    """Compare two version strings. Returns -1, 0, or 1."""
    parts_a = _parse_version(a)
    parts_b = _parse_version(b)
    for pa, pb in zip(parts_a, parts_b):
        if pa < pb:
            return -1
        if pa > pb:
            return 1
    if len(parts_a) < len(parts_b):
        return -1
    if len(parts_a) > len(parts_b):
        return 1
    return 0


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse version string into comparable tuple."""
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", v)
    if not match:
        return (0, 0, 0)
    return tuple(int(x) for x in match.groups())


def _parse_major(v: str) -> int:
    return _parse_version(v)[0] if _parse_version(v) else 0


def _platform_key() -> str:
    """Get platform key for download URL lookup."""
    os_name = platform.system().lower()
    machine = platform.machine().lower()
    if os_name == "windows":
        return "windows-x64" if "64" in machine else "windows-x86"
    if os_name == "linux":
        return "linux-x64" if "64" in machine else "linux-x86"
    return f"{os_name}-{machine}"
