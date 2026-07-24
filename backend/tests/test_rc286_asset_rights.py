"""RC ID: RC-286. Tests for asset publication rights."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs" / "legal" / "asset-publication-rights.yml"
RABBIT_ART_LICENSE = ROOT / "docs" / "legal" / "rabbit-art-license.yml"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc286_asset_rights.py"

REQUIRED_CATEGORIES = [
    "rabbit_artwork",
    "app_icons",
    "fonts",
    "screenshots",
    "doc_images",
    "demo_repo",
]


class TestRegister:
    def test_exists(self) -> None:
        assert REGISTER.is_file()

    def test_has_all_categories(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        categories = data.get("categories", {})
        for cat in REQUIRED_CATEGORIES:
            assert cat in categories, f"Missing category: {cat}"

    def test_all_confirmed(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        assert data.get("all_categories_confirmed") is True

    def test_no_blocking_categories(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        assert data.get("blocking_categories") == []


class TestRabbitArtwork:
    def test_category_exists(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        assert "rabbit_artwork" in data.get("categories", {})

    def test_status_authorized(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        artwork = data["categories"]["rabbit_artwork"]
        assert artwork["status"] == "user-authorized"

    def test_links_to_rc035(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        artwork = data["categories"]["rabbit_artwork"]
        assert "rabbit-art-license" in artwork["evidence_path"]

    def test_rc035_evidence_exists(self) -> None:
        assert RABBIT_ART_LICENSE.is_file()


class TestAppIcons:
    def test_category_exists(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        assert "app_icons" in data.get("categories", {})

    def test_status_project_created(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        icons = data["categories"]["app_icons"]
        assert icons["status"] == "project-created"

    def test_license_mit(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        icons = data["categories"]["app_icons"]
        assert icons["license"] == "MIT"

    def test_icon_files_exist(self) -> None:
        assert (ROOT / "apps" / "desktop" / "src-tauri" / "icons" / "icon.ico").is_file()
        assert (ROOT / "apps" / "desktop" / "src-tauri" / "icons" / "icon.png").is_file()
        assert (ROOT / "frontend" / "public" / "favicon.svg").is_file()


class TestFonts:
    def test_category_exists(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        assert "fonts" in data.get("categories", {})

    def test_not_applicable(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        fonts = data["categories"]["fonts"]
        assert fonts["status"] == "not-applicable"

    def test_no_assets(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        fonts = data["categories"]["fonts"]
        assert fonts["assets"] == []


class TestScreenshots:
    def test_category_exists(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        assert "screenshots" in data.get("categories", {})

    def test_status_project_created(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        screenshots = data["categories"]["screenshots"]
        assert screenshots["status"] == "project-created"


class TestDocImages:
    def test_category_exists(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        assert "doc_images" in data.get("categories", {})

    def test_license_mit(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        doc_images = data["categories"]["doc_images"]
        assert doc_images["license"] == "MIT"


class TestDemoRepo:
    def test_category_exists(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        assert "demo_repo" in data.get("categories", {})

    def test_license_mit(self) -> None:
        data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        demo = data["categories"]["demo_repo"]
        assert demo["license"] == "MIT"


class TestCheckScript:
    def test_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_has_all_checks(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_register_exists" in text
        assert "check_all_categories" in text
        assert "check_all_confirmed" in text
        assert "check_rabbit_artwork_evidence" in text
        assert "check_icons_exist" in text
        assert "check_fonts_not_applicable" in text
