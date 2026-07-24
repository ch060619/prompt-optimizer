"""RC ID: RC-292. Tests for architecture prototype minimal closed loop."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = {
    "agent_core": "backend/rabbit_code/agent.py",
    "app_server": "backend/rabbit_code/prototype_app.py",
    "cli": "backend/rabbit_code/cli.py",
    "process_tools": "backend/rabbit_code/process_tools.py",
    "sidecar": "backend/rabbit_code/sidecar.py",
    "shared_surface": "backend/rabbit_code/shared_surface.py",
    "agent_state": "backend/rabbit_code/agent_state.py",
    "streaming": "backend/rabbit_code/streaming.py",
    "runtime": "backend/rabbit_code/runtime.py",
    "tauri_conf": "apps/desktop/src-tauri/tauri.conf.json",
    "tauri_main": "apps/desktop/src-tauri/src/main.rs",
    "frontend_app": "frontend/src/App.tsx",
}

CHECK_SCRIPT = ROOT / "scripts" / "check_rc292_prototype.py"


class TestFilesExist:
    @pytest.mark.parametrize("name,rel_path", list(REQUIRED_FILES.items()))
    def test_file_exists(self, name: str, rel_path: str) -> None:
        assert (ROOT / rel_path).is_file(), f"Missing {name}: {rel_path}"


class TestAgentCore:
    def test_has_agent_core_class(self) -> None:
        text = (ROOT / "backend/rabbit_code/agent.py").read_text(encoding="utf-8")
        assert "AgentCore" in text

    def test_has_agent_event_type(self) -> None:
        text = (ROOT / "backend/rabbit_code/agent.py").read_text(encoding="utf-8")
        assert "AgentEventType" in text


class TestAppServer:
    def test_uses_fastapi(self) -> None:
        text = (ROOT / "backend/rabbit_code/prototype_app.py").read_text(encoding="utf-8")
        assert "FastAPI" in text or "fastapi" in text

    def test_has_create_app(self) -> None:
        text = (ROOT / "backend/rabbit_code/prototype_app.py").read_text(encoding="utf-8")
        assert "create_app" in text

    def test_has_routes(self) -> None:
        text = (ROOT / "backend/rabbit_code/prototype_app.py").read_text(encoding="utf-8")
        assert "@" in text or "route" in text.lower()


class TestCLI:
    def test_has_run_function(self) -> None:
        text = (ROOT / "backend/rabbit_code/cli.py").read_text(encoding="utf-8")
        assert "def run" in text or "def main" in text


class TestProcessManagement:
    def test_sidecar_exists(self) -> None:
        text = (ROOT / "backend/rabbit_code/sidecar.py").read_text(encoding="utf-8")
        assert len(text) > 0

    def test_process_tools_exists(self) -> None:
        text = (ROOT / "backend/rabbit_code/process_tools.py").read_text(encoding="utf-8")
        assert len(text) > 0


class TestProtocolGeneration:
    def test_shared_surface_exists(self) -> None:
        text = (ROOT / "backend/rabbit_code/shared_surface.py").read_text(encoding="utf-8")
        assert len(text) > 0


class TestTauriGUI:
    def test_tauri_conf_exists(self) -> None:
        assert (ROOT / "apps/desktop/src-tauri/tauri.conf.json").is_file()

    def test_tauri_main_exists(self) -> None:
        assert (ROOT / "apps/desktop/src-tauri/src/main.rs").is_file()

    def test_frontend_app_exists(self) -> None:
        assert (ROOT / "frontend/src/App.tsx").is_file()


class TestExistingPrototypeTests:
    def test_rc057_test_exists(self) -> None:
        assert (ROOT / "backend/tests/test_rc057_agent_prototype.py").is_file()

    def test_rc230_test_exists(self) -> None:
        assert (ROOT / "backend/tests/test_rc230_agent_core.py").is_file()


class TestCheckScript:
    def test_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_has_all_checks(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_files_exist" in text
        assert "check_classes_exist" in text
        assert "check_tests_exist" in text
        assert "check_tauri_gui" in text
        assert "check_process_management" in text
        assert "check_protocol_generation" in text
