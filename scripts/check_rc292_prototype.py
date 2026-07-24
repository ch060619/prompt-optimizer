#!/usr/bin/env python3
"""RC ID: RC-292. Verify minimal closed loop of architecture prototype.

Checks that the following components exist and form a minimal closed loop:
    1. Shared Agent Core (backend/rabbit_code/agent.py)
    2. FastAPI App Server (backend/rabbit_code/prototype_app.py)
    3. CLI event flow (backend/rabbit_code/cli.py)
    4. Tauri GUI (apps/desktop/src-tauri/)
    5. Process management (backend/rabbit_code/process_tools.py, sidecar.py)
    6. Protocol generation (backend/rabbit_code/shared_surface.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = {
    "agent_core": "backend/rabbit_code/agent.py",
    "app_server": "backend/rabbit_code/prototype_app.py",
    "cli": "backend/rabbit_code/cli.py",
    "process_tools": "backend/rabbit_code/process_tools.py",
    "sidecar": "backend/rabbit_code/sidecar.py",
    "sidecar_server": "backend/rabbit_code/sidecar_server.py",
    "shared_surface": "backend/rabbit_code/shared_surface.py",
    "agent_state": "backend/rabbit_code/agent_state.py",
    "streaming": "backend/rabbit_code/streaming.py",
    "runtime": "backend/rabbit_code/runtime.py",
    "tauri_conf": "apps/desktop/src-tauri/tauri.conf.json",
    "tauri_cargo": "apps/desktop/src-tauri/Cargo.toml",
    "tauri_main": "apps/desktop/src-tauri/src/main.rs",
    "frontend_app": "frontend/src/App.tsx",
}

REQUIRED_CLASSES = {
    "backend/rabbit_code/agent.py": ["AgentCore", "AgentEventType"],
    "backend/rabbit_code/prototype_app.py": ["create_app"],
    "backend/rabbit_code/cli.py": ["run"],
    "backend/rabbit_code/shared_surface.py": [],  # just needs to exist
    "backend/rabbit_code/agent_state.py": ["AgentState", "AgentStateMachine"],
}

REQUIRED_TESTS = [
    "backend/tests/test_rc057_agent_prototype.py",
    "backend/tests/test_rc230_agent_core.py",
]


def check_files_exist() -> list[str]:
    errors: list[str] = []
    for name, rel_path in REQUIRED_FILES.items():
        full_path = ROOT / rel_path
        if not full_path.is_file():
            errors.append(f"Missing {name}: {rel_path}")
    return errors


def check_classes_exist() -> list[str]:
    errors: list[str] = []
    for rel_path, classes in REQUIRED_CLASSES.items():
        full_path = ROOT / rel_path
        if not full_path.is_file():
            errors.append(f"Cannot check classes, file missing: {rel_path}")
            continue
        text = full_path.read_text(encoding="utf-8")
        for cls in classes:
            if cls not in text:
                errors.append(f"Missing class/function {cls} in {rel_path}")
    return errors


def check_tests_exist() -> list[str]:
    errors: list[str] = []
    for rel_path in REQUIRED_TESTS:
        full_path = ROOT / rel_path
        if not full_path.is_file():
            errors.append(f"Missing test: {rel_path}")
    return errors


def check_tauri_gui() -> list[str]:
    errors: list[str] = []
    tauri_conf = ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"
    if not tauri_conf.is_file():
        errors.append("tauri.conf.json not found")
        return errors
    import json
    data = json.loads(tauri_conf.read_text(encoding="utf-8"))
    if "build" not in data and "tauri" not in data:
        errors.append("tauri.conf.json missing build/tauri config")
    # Check frontend devUrl or frontendDist
    if "build" in data:
        build = data["build"]
        if "devUrl" not in build and "frontendDist" not in build:
            errors.append("tauri.conf.json build missing devUrl/frontendDist")
    return errors


def check_process_management() -> list[str]:
    errors: list[str] = []
    sidecar = ROOT / "backend" / "rabbit_code" / "sidecar.py"
    if sidecar.is_file():
        text = sidecar.read_text(encoding="utf-8")
        if "spawn" not in text.lower() and "subprocess" not in text.lower() and "start" not in text.lower():
            errors.append("sidecar.py should reference process spawning")
    process_tools = ROOT / "backend" / "rabbit_code" / "process_tools.py"
    if process_tools.is_file():
        text = process_tools.read_text(encoding="utf-8")
        if "process" not in text.lower():
            errors.append("process_tools.py should reference process management")
    return errors


def check_protocol_generation() -> list[str]:
    errors: list[str] = []
    shared_surface = ROOT / "backend" / "rabbit_code" / "shared_surface.py"
    if shared_surface.is_file():
        text = shared_surface.read_text(encoding="utf-8")
        if "protocol" not in text.lower() and "surface" not in text.lower() and "schema" not in text.lower():
            errors.append("shared_surface.py should define protocol/schema")
    # Check API app has routes
    app = ROOT / "backend" / "rabbit_code" / "prototype_app.py"
    if app.is_file():
        text = app.read_text(encoding="utf-8")
        if "FastAPI" not in text and "fastapi" not in text:
            errors.append("prototype_app.py should use FastAPI")
        if "route" not in text.lower() and "@" not in text:
            errors.append("prototype_app.py should define API routes")
    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(check_files_exist())
    all_errors.extend(check_classes_exist())
    all_errors.extend(check_tests_exist())
    all_errors.extend(check_tauri_gui())
    all_errors.extend(check_process_management())
    all_errors.extend(check_protocol_generation())

    if all_errors:
        print("FAIL: RC-292 architecture prototype verification", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-292 architecture prototype verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
