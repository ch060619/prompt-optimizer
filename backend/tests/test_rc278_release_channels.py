"""RC ID: RC-278. Validate release channels, changelog, and migration gates."""

from __future__ import annotations

from pathlib import Path

from prompt_optimizer.release_channels import (
    CHANNEL_CONFIGS,
    CHANNEL_PATTERNS,
    CHANNEL_ROLLOUT,
    ChannelConfig,
    MigrationGate,
    get_channel_config,
    parse_channel_from_version,
    validate_version_for_channel,
)

ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = ROOT / "CHANGELOG.md"


class TestChannelPatterns:
    def test_stable_pattern(self) -> None:
        assert validate_version_for_channel("3.0.0", "stable") is True

    def test_stable_pattern_rejects_beta(self) -> None:
        assert validate_version_for_channel("3.0.0-beta.1", "stable") is False

    def test_beta_pattern(self) -> None:
        assert validate_version_for_channel("3.1.0-beta.1", "beta") is True

    def test_nightly_pattern(self) -> None:
        assert validate_version_for_channel("3.2.0-dev.20260722", "nightly") is True


class TestParseChannel:
    def test_parse_stable(self) -> None:
        assert parse_channel_from_version("3.0.0") == "stable"

    def test_parse_beta(self) -> None:
        assert parse_channel_from_version("3.1.0-beta.1") == "beta"

    def test_parse_nightly(self) -> None:
        assert parse_channel_from_version("3.2.0-dev.20260722") == "nightly"

    def test_parse_unknown_defaults_stable(self) -> None:
        assert parse_channel_from_version("unknown") == "stable"


class TestChannelConfigs:
    def test_stable_config(self) -> None:
        config = get_channel_config("stable")
        assert config.rollout_percentage == 100
        assert config.min_schema_version == 2

    def test_beta_config(self) -> None:
        config = get_channel_config("beta")
        assert config.rollout_percentage == 25

    def test_nightly_config(self) -> None:
        config = get_channel_config("nightly")
        assert config.rollout_percentage == 10
        assert config.min_schema_version == 1

    def test_all_channels_have_configs(self) -> None:
        for ch in ("stable", "beta", "nightly"):
            assert ch in CHANNEL_CONFIGS

    def test_all_channels_have_rollout(self) -> None:
        for ch in ("stable", "beta", "nightly"):
            assert ch in CHANNEL_ROLLOUT


class TestMigrationGate:
    def test_can_start_current_version(self) -> None:
        gate = MigrationGate(current_schema_version=2, target_schema_version=2)
        assert gate.can_start() is True

    def test_needs_migration(self) -> None:
        gate = MigrationGate(current_schema_version=1, target_schema_version=2)
        assert gate.needs_migration() is True

    def test_no_migration_needed(self) -> None:
        gate = MigrationGate(current_schema_version=2, target_schema_version=2)
        assert gate.needs_migration() is False

    def test_incompatible_newer_db(self) -> None:
        gate = MigrationGate(current_schema_version=3, target_schema_version=2)
        assert gate.is_incompatible() is True
        assert gate.can_start() is False

    def test_status_up_to_date(self) -> None:
        gate = MigrationGate(current_schema_version=2, target_schema_version=2)
        assert "up to date" in gate.get_status()

    def test_status_needs_migration(self) -> None:
        gate = MigrationGate(current_schema_version=1, target_schema_version=2)
        assert "migrated" in gate.get_status()

    def test_status_incompatible(self) -> None:
        gate = MigrationGate(current_schema_version=3, target_schema_version=2)
        assert "newer" in gate.get_status()
        assert "Downgrade not supported" in gate.get_status()

    def test_zero_version_cannot_start(self) -> None:
        gate = MigrationGate(current_schema_version=0, target_schema_version=2)
        assert gate.can_start() is False


class TestChangelog:
    def test_changelog_exists(self) -> None:
        assert CHANGELOG.is_file()

    def test_changelog_has_semver(self) -> None:
        content = CHANGELOG.read_text(encoding="utf-8")
        assert "Semantic Versioning" in content

    def test_changelog_has_channels(self) -> None:
        content = CHANGELOG.read_text(encoding="utf-8")
        assert "nightly" in content
        assert "beta" in content
        assert "stable" in content

    def test_changelog_has_3_0_0(self) -> None:
        content = CHANGELOG.read_text(encoding="utf-8")
        assert "[3.0.0]" in content
