from __future__ import annotations

import hashlib
import json
from pathlib import Path

from prompt_optimizer.providers import ModelRequest
from rabbit_code.plugins import PluginRegistry

from examples.mcp_server import respond
from examples.provider_adapter import ExampleAdapter
from examples.tool import workspace_summary


ROOT = Path(__file__).parent


def test_provider_adapter_is_deterministic_and_streams() -> None:
    adapter = ExampleAdapter()
    request = ModelRequest(prompt="Explain a test in one sentence.")
    result = adapter.optimize(request)
    events = tuple(adapter.stream(request))

    assert result.provider_used == "example-local"
    assert events[0].type.value == "started"
    assert events[-1].type.value == "completed"


def test_workspace_tool_is_bounded_and_read_only(tmp_path: Path) -> None:
    (tmp_path / "one.txt").write_text("one", encoding="utf-8")
    (tmp_path / "two.txt").write_text("two", encoding="utf-8")

    result = workspace_summary(tmp_path, limit=1)

    assert result["file_count"] == 1
    assert len(result["files"]) == 1


def test_mcp_manifest_and_theme_are_local_minimal_examples() -> None:
    mcp = json.loads((ROOT / "mcp-server.json").read_text(encoding="utf-8"))
    theme = json.loads((ROOT / "theme" / "theme.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "plugin" / "manifest.json").read_text(encoding="utf-8"))

    assert mcp["transport"] == "stdio"
    assert mcp["permissions"] == ["read"]
    assert theme["scope"] == "workspace"
    assert manifest["permissions"] == ["read"]
    assert manifest["sha256"] == hashlib.sha256((ROOT / "plugin" / "plugin.py").read_bytes()).hexdigest()


def test_mcp_response_and_plugin_registry_contract(tmp_path: Path) -> None:
    initialized = respond({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    called = respond(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "example_status", "arguments": {}},
        }
    )
    registry = PluginRegistry(
        tmp_path / "plugins",
        handlers={"handle": lambda context: context.payload},
        allowed_permissions={"read"},
    )
    registry.install(ROOT / "plugin")
    registry.enable("example-read-plugin")

    assert initialized["result"]["capabilities"] == {"tools": {}}
    assert called["result"]["content"][0]["text"] == "ready"
    assert registry.execute("example-read-plugin", {"prompt": "local"}) == {"prompt": "local"}
