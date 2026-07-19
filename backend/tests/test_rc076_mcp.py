from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from backend.rabbit_code.mcp import (
    McpAuthError,
    McpCancelled,
    McpClient,
    McpServerConfig,
    McpTool,
    McpTransportError,
    StdioMcpTransport,
)

# RC ID: RC-076. Verify MCP config, tool mapping, auth, reconnect, cancel, and cleanup.


class FakeTransport:
    def __init__(self, *, fail_once: bool = False) -> None:
        self.fail_once = fail_once
        self.connect_count = 0
        self.closed = False
        self.cancelled = False
        self.calls: list[str] = []

    def connect(self, auth_token: str | None = None) -> None:
        self.connect_count += 1
        self.closed = False

    def request(self, method, params, cancellation):  # type: ignore[no-untyped-def]
        self.calls.append(method)
        if cancellation.is_set():
            raise McpCancelled("cancelled")
        if self.fail_once:
            self.fail_once = False
            raise McpTransportError("temporary disconnect")
        if method == "initialize":
            return {"capabilities": {"tools": True}}
        if method == "tools/list":
            return {
                "tools": [
                    {"name": "read_file", "description": "Read", "readOnly": True},
                    {"name": "write_file", "description": "Write", "readOnly": False},
                ]
            }
        return {"content": [{"type": "text", "text": "ok"}]}

    def cancel(self) -> None:
        self.cancelled = True

    def close(self) -> None:
        self.closed = True


def test_mcp_maps_tools_and_rejects_unauthorized_write() -> None:
    transport = FakeTransport()
    client = McpClient(
        McpServerConfig(name="demo", transport="stdio", command=("demo",)),
        transport=transport,
    )

    client.connect()

    assert client.tools == (
        McpTool("read_file", "Read", {}, True),
        McpTool("write_file", "Write", {}, False),
    )
    assert client.call_tool("read_file", {})["content"]
    with pytest.raises(PermissionError, match="write permission"):
        client.call_tool("write_file", {})
    client.close()
    assert transport.closed


def test_mcp_config_project_overrides_user_and_auth_is_required(tmp_path: Path) -> None:
    user = tmp_path / "user.json"
    project = tmp_path / "project.json"
    user.write_text(
        json.dumps(
            {
                "servers": {
                    "demo": {
                        "transport": "streamable_http",
                        "url": "http://user",
                        "require_auth": True,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    project.write_text(
        json.dumps({"servers": {"demo": {"url": "http://project"}}}),
        encoding="utf-8",
    )

    config = McpServerConfig.from_files(user, project, "demo")

    assert config.url == "http://project"
    with pytest.raises(McpAuthError, match="authentication token"):
        McpClient(config, transport=FakeTransport()).connect()


def test_mcp_reconnects_once_after_transport_failure() -> None:
    transport = FakeTransport(fail_once=True)
    client = McpClient(
        McpServerConfig(name="demo", transport="stdio", command=("demo",), max_retries=1),
        transport=transport,
    )

    client.connect()

    assert client.capabilities == {"tools": True}
    assert transport.connect_count == 2


def test_mcp_cancel_propagates_and_close_is_idempotent() -> None:
    transport = FakeTransport()
    client = McpClient(
        McpServerConfig(name="demo", transport="stdio", command=("demo",)),
        transport=transport,
    )
    client.connect()
    client.cancel()

    with pytest.raises(McpCancelled):
        client.list_tools()
    assert transport.cancelled
    client.close()
    client.close()


def test_stdio_transport_terminates_child_process() -> None:
    transport = StdioMcpTransport(
        (
            sys.executable,
            "-c",
            "import time; time.sleep(30)",
        )
    )
    transport.connect()
    process = transport.process
    assert process is not None and process.poll() is None

    transport.close()

    assert process.poll() is not None
