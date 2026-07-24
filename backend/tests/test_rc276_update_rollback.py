"""RC ID: RC-276. Validate secure update check and rollback."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from prompt_optimizer.update_checker import (
    RollbackManager,
    UpdateChecker,
    UpdateInfo,
    check_version_compatibility,
    _compare_versions,
    _parse_version,
)

ROOT = Path(__file__).resolve().parents[2]
UPDATE_MANIFEST = ROOT / "scripts" / "install" / "update-manifest.json"


class TestVersionComparison:
    def test_same_version(self) -> None:
        assert _compare_versions("3.0.0", "3.0.0") == 0

    def test_newer_version(self) -> None:
        assert _compare_versions("3.1.0", "3.0.0") == 1

    def test_older_version(self) -> None:
        assert _compare_versions("2.9.0", "3.0.0") == -1

    def test_parse_version(self) -> None:
        assert _parse_version("3.0.1") == (3, 0, 1)

    def test_parse_invalid_version(self) -> None:
        assert _parse_version("invalid") == (0, 0, 0)


class TestUpdateInfo:
    def test_update_available(self) -> None:
        info = UpdateInfo(
            current_version="3.0.0",
            latest_version="3.1.0",
            download_url="https://example.com",
            sha256="abc",
            release_notes="test",
            channel="stable",
        )
        assert info.update_available is True

    def test_no_update_available(self) -> None:
        info = UpdateInfo(
            current_version="3.1.0",
            latest_version="3.1.0",
            download_url="",
            sha256="",
            release_notes="",
            channel="stable",
        )
        assert info.update_available is False

    def test_is_breaking(self) -> None:
        info = UpdateInfo(
            current_version="3.0.0",
            latest_version="4.0.0",
            download_url="",
            sha256="",
            release_notes="",
            channel="stable",
            breaking_changes=["API changed"],
        )
        assert info.is_breaking is True


class TestUpdateChecker:
    def test_verify_download_correct_hash(self) -> None:
        checker = UpdateChecker("3.0.0")
        data = b"test data"
        expected = hashlib.sha256(data).hexdigest()
        assert checker.verify_download(data, expected) is True

    def test_verify_download_wrong_hash(self) -> None:
        checker = UpdateChecker("3.0.0")
        assert checker.verify_download(b"test", "wrong") is False

    def test_should_offer_update_full_rollout(self) -> None:
        checker = UpdateChecker("3.0.0")
        update = UpdateInfo(
            current_version="3.0.0",
            latest_version="3.1.0",
            download_url="",
            sha256="",
            release_notes="",
            channel="stable",
            rollout_percentage=100,
        )
        assert checker.should_offer_update(update, user_rollout_id=99) is True

    def test_should_offer_update_partial_rollout(self) -> None:
        checker = UpdateChecker("3.0.0")
        update = UpdateInfo(
            current_version="3.0.0",
            latest_version="3.1.0",
            download_url="",
            sha256="",
            release_notes="",
            channel="beta",
            rollout_percentage=25,
        )
        # user 0 should get it (0 < 25)
        assert checker.should_offer_update(update, user_rollout_id=0) is True
        # user 50 should not (50 >= 25)
        assert checker.should_offer_update(update, user_rollout_id=50) is False

    def test_check_returns_none_on_network_error(self) -> None:
        checker = UpdateChecker("3.0.0")
        # Will fail to fetch manifest, should return None
        result = checker.check()
        assert result is None


class TestVersionCompatibility:
    def test_compatible_upgrade(self) -> None:
        compat = check_version_compatibility("3.0.0", "3.1.0")
        assert compat.is_compatible is True
        assert len(compat.warnings) == 0

    def test_incompatible_min_version(self) -> None:
        compat = check_version_compatibility("2.0.0", "3.0.0", min_required="2.5.0")
        assert compat.is_compatible is False
        assert len(compat.warnings) == 1

    def test_major_version_jump_warning(self) -> None:
        compat = check_version_compatibility("3.0.0", "6.0.0")
        assert compat.is_compatible is True
        assert len(compat.warnings) == 1

    def test_format_hints(self) -> None:
        compat = check_version_compatibility("3.0.0", "3.1.0")
        hints = compat.format_hints()
        assert "compatible" in hints


class TestRollbackManager:
    def test_list_backups_empty(self, tmp_path: Path) -> None:
        manager = RollbackManager(str(tmp_path))
        assert manager.list_backups() == []

    def test_backup_and_list(self, tmp_path: Path) -> None:
        (tmp_path / "test.txt").write_text("current")
        manager = RollbackManager(str(tmp_path))
        manager.backup_current("3.0.0")
        backups = manager.list_backups()
        assert "3.0.0" in backups

    def test_rollback_to_nonexistent(self, tmp_path: Path) -> None:
        manager = RollbackManager(str(tmp_path))
        assert manager.rollback_to("nonexistent") is False

    def test_rollback_restores_files(self, tmp_path: Path) -> None:
        (tmp_path / "app.txt").write_text("original")
        manager = RollbackManager(str(tmp_path))
        manager.backup_current("3.0.0")
        # Modify current
        (tmp_path / "app.txt").write_text("modified")
        # Rollback
        assert manager.rollback_to("3.0.0") is True
        assert (tmp_path / "app.txt").read_text() == "original"


class TestManifest:
    def test_manifest_valid_json(self) -> None:
        manifest = json.loads(UPDATE_MANIFEST.read_text(encoding="utf-8"))
        assert "channels" in manifest

    def test_manifest_has_stable_channel(self) -> None:
        manifest = json.loads(UPDATE_MANIFEST.read_text(encoding="utf-8"))
        assert "stable" in manifest["channels"]

    def test_manifest_has_beta_channel(self) -> None:
        manifest = json.loads(UPDATE_MANIFEST.read_text(encoding="utf-8"))
        assert "beta" in manifest["channels"]

    def test_manifest_has_nightly_channel(self) -> None:
        manifest = json.loads(UPDATE_MANIFEST.read_text(encoding="utf-8"))
        assert "nightly" in manifest["channels"]

    def test_manifest_channels_have_rollout(self) -> None:
        manifest = json.loads(UPDATE_MANIFEST.read_text(encoding="utf-8"))
        for ch_name, ch_info in manifest["channels"].items():
            assert "rollout_percentage" in ch_info, f"{ch_name} missing rollout_percentage"
