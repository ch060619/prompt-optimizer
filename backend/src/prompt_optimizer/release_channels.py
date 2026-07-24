"""RC ID: RC-278. Release channel management and database migration gates.

Ensures the application refuses to start if the database schema version
is incompatible with the current application version.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from prompt_optimizer.storage.migrations import TARGET_SCHEMA_VERSION

__all__ = [
    "ReleaseChannel",
    "ChannelConfig",
    "MigrationGate",
    "parse_channel_from_version",
    "validate_version_for_channel",
]

ReleaseChannel = Literal["stable", "beta", "nightly"]

CHANNEL_PATTERNS: dict[ReleaseChannel, str] = {
    "stable": r"^\d+\.\d+\.\d+$",
    "beta": r"^\d+\.\d+\.\d+-beta\.\d+$",
    "nightly": r"^\d+\.\d+\.\d+-dev\.\d+$",
}

CHANNEL_ROLLOUT: dict[ReleaseChannel, int] = {
    "stable": 100,
    "beta": 25,
    "nightly": 10,
}


@dataclass
class ChannelConfig:
    """Configuration for a release channel."""

    channel: ReleaseChannel
    version_pattern: str
    rollout_percentage: int
    min_schema_version: int
    description: str


CHANNEL_CONFIGS: dict[ReleaseChannel, ChannelConfig] = {
    "stable": ChannelConfig(
        channel="stable",
        version_pattern=CHANNEL_PATTERNS["stable"],
        rollout_percentage=100,
        min_schema_version=2,
        description="Production-ready release",
    ),
    "beta": ChannelConfig(
        channel="beta",
        version_pattern=CHANNEL_PATTERNS["beta"],
        rollout_percentage=25,
        min_schema_version=2,
        description="Feature-complete, testing channel",
    ),
    "nightly": ChannelConfig(
        channel="nightly",
        version_pattern=CHANNEL_PATTERNS["nightly"],
        rollout_percentage=10,
        min_schema_version=1,
        description="Experimental development builds",
    ),
}


@dataclass
class MigrationGate:
    """Gate that checks database schema compatibility before startup."""

    current_schema_version: int
    target_schema_version: int = TARGET_SCHEMA_VERSION

    def can_start(self) -> bool:
        """Returns True if the database is compatible with the current app."""
        return self.current_schema_version >= 1 and self.current_schema_version <= self.target_schema_version

    def needs_migration(self) -> bool:
        """Returns True if the database needs to be migrated."""
        return self.current_schema_version < self.target_schema_version

    def is_incompatible(self) -> bool:
        """Returns True if the database is from a newer version (incompatible)."""
        return self.current_schema_version > self.target_schema_version

    def get_status(self) -> str:
        """Get human-readable migration gate status."""
        if self.is_incompatible():
            return (
                f"Database schema v{self.current_schema_version} is newer than "
                f"supported v{self.target_schema_version}. Downgrade not supported. "
                f"Please upgrade Rabbit Code or restore from backup."
            )
        if self.needs_migration():
            return (
                f"Database schema v{self.current_schema_version} will be migrated "
                f"to v{self.target_schema_version}."
            )
        return f"Database schema v{self.current_schema_version} is up to date."


def parse_channel_from_version(version: str) -> ReleaseChannel:
    """Determine the release channel from a version string."""
    for channel, pattern in CHANNEL_PATTERNS.items():
        if re.match(pattern, version):
            return channel
    # Default to stable for unrecognized versions
    return "stable"


def validate_version_for_channel(version: str, channel: ReleaseChannel) -> bool:
    """Validate that a version string matches the expected channel pattern."""
    pattern = CHANNEL_PATTERNS.get(channel)
    if not pattern:
        return False
    return bool(re.match(pattern, version))


def get_channel_config(channel: ReleaseChannel) -> ChannelConfig:
    """Get configuration for a release channel."""
    return CHANNEL_CONFIGS[channel]
