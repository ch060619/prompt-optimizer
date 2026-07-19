from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event, Lock
from types import MappingProxyType
from typing import Any, Protocol

import httpx

# RC ID: RC-076. Own the approved MCP transport and tool lifecycle boundary.


class McpTransportError(RuntimeError):
    pass


class McpAuthError(McpTransportError):
    pass


class McpCancelled(McpTransportError):
    pass


@dataclass(frozen=True)
class McpServerConfig:
    name: str
    transport: str
    command: tuple[str, ...] = ()
    url: str | None = None
    require_auth: bool = False
    auth_token: str | None = field(default=None, repr=False)
    write_authorized: bool = False
    max_retries: int = 2

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("MCP server name is required")
        if self.transport not in {"stdio", "streamable_http"}:
            raise ValueError("unsupported MCP transport")
        if self.transport == "stdio" and not self.command:
            raise ValueError("stdio MCP server requires a command")
        if self.transport == "streamable_http" and not self.url:
            raise ValueError("streamable HTTP MCP server requires a URL")
        if self.max_retries < 0:
            raise ValueError("MCP max_retries must be non-negative")

    @classmethod
    def from_files(
        cls,
        user_path: Path | None,
        project_path: Path | None,
        name: str,
    ) -> McpServerConfig:
        merged: dict[str, Any] = {}
        for path in (user_path, project_path):
            if path is None or not path.is_file():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            servers = payload.get("servers") if isinstance(payload, dict) else None
            item = servers.get(name) if isinstance(servers, dict) else None
            if item is not None:
                if not isinstance(item, dict):
                    raise ValueError("MCP server config must be an object")
                merged.update(item)
        if not merged:
            raise ValueError(f"MCP server config not found: {name}")
        raw_command = merged.get("command", ())
        command = tuple(raw_command) if isinstance(raw_command, list) else tuple(raw_command)
        values = {key: value for key, value in merged.items() if key != "command"}
        return cls(name=name, command=command, **values)


@dataclass(frozen=True)
class McpTool:
    name: str
    description: str
    input_schema: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("MCP tool name is required")
        object.__setattr__(self, "input_schema", MappingProxyType(dict(self.input_schema)))


class McpTransport(Protocol):
    def connect(self, auth_token: str | None = None) -> None:
        pass

    def request(
        self,
        method: str,
        params: Mapping[str, Any],
        cancellation: Event,
    ) -> Mapping[str, Any]:
        pass

    def cancel(self) -> None:
        pass

    def close(self) -> None:
        pass


class StdioMcpTransport:
    def __init__(self, command: Sequence[str]) -> None:
        if not command or any(not isinstance(item, str) or not item for item in command):
            raise ValueError("stdio MCP command must contain non-empty strings")
        self.command = tuple(command)
        self.process: subprocess.Popen[str] | None = None
        self._next_id = 0
        self._lock = Lock()

    def connect(self, auth_token: str | None = None) -> None:
        del auth_token
        if self.process is not None and self.process.poll() is None:
            return
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                shell=False,
            )
        except OSError as exc:
            raise McpTransportError(f"failed to start MCP stdio server: {exc}") from exc

    def request(
        self,
        method: str,
        params: Mapping[str, Any],
        cancellation: Event,
    ) -> Mapping[str, Any]:
        if cancellation.is_set():
            raise McpCancelled("MCP request cancelled")
        process = self.process
        if (
            process is None
            or process.poll() is not None
            or process.stdin is None
            or process.stdout is None
        ):
            raise McpTransportError("MCP stdio server is not connected")
        with self._lock:
            request_id = self._next_id
            self._next_id += 1
            try:
                process.stdin.write(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "method": method,
                            "params": dict(params),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                process.stdin.flush()
                line = process.stdout.readline()
            except OSError as exc:
                raise McpTransportError(f"MCP stdio request failed: {exc}") from exc
        if not line:
            raise McpTransportError("MCP stdio server closed its output")
        try:
            response = json.loads(line)
        except json.JSONDecodeError as exc:
            raise McpTransportError("MCP stdio returned invalid JSON") from exc
        return _rpc_result(response)

    def cancel(self) -> None:
        self.close()

    def close(self) -> None:
        process = self.process
        self.process = None
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)


class StreamableHttpMcpTransport:
    def __init__(self, url: str, client: httpx.Client | None = None) -> None:
        self.url = url
        self.client = client or httpx.Client()
        self.auth_token: str | None = None
        self._next_id = 0

    def connect(self, auth_token: str | None = None) -> None:
        self.auth_token = auth_token

    def request(
        self,
        method: str,
        params: Mapping[str, Any],
        cancellation: Event,
    ) -> Mapping[str, Any]:
        if cancellation.is_set():
            raise McpCancelled("MCP request cancelled")
        headers = {"Accept": "application/json, text/event-stream"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        request_id = self._next_id
        self._next_id += 1
        try:
            response = self.client.post(
                self.url,
                headers=headers,
                json={"jsonrpc": "2.0", "id": request_id, "method": method, "params": dict(params)},
            )
            if response.status_code in {401, 403}:
                raise McpAuthError("MCP server rejected authentication")
            response.raise_for_status()
            payload = response.json()
        except McpAuthError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise McpTransportError(f"MCP HTTP request failed: {exc}") from exc
        return _rpc_result(payload)

    def cancel(self) -> None:
        pass

    def close(self) -> None:
        self.client.close()


class McpClient:
    def __init__(self, config: McpServerConfig, *, transport: McpTransport | None = None) -> None:
        self.config = config
        self.transport = transport or _transport_for(config)
        self._cancel = Event()
        self._connected = False
        self._capabilities: Mapping[str, Any] = MappingProxyType({})
        self._tools: tuple[McpTool, ...] = ()

    @property
    def capabilities(self) -> Mapping[str, Any]:
        return self._capabilities

    @property
    def tools(self) -> tuple[McpTool, ...]:
        return self._tools

    def connect(self) -> None:
        if self.config.require_auth and not self.config.auth_token:
            raise McpAuthError("MCP server requires an authentication token")
        self._cancel.clear()
        try:
            self.transport.connect(self.config.auth_token)
        except McpTransportError:
            raise
        except OSError as exc:
            raise McpTransportError(str(exc)) from exc
        self._capabilities = MappingProxyType(
            dict(self._request("initialize", {"protocolVersion": "v1"}).get("capabilities", {}))
        )
        self._tools = self._map_tools(self._request("tools/list", {}))
        self._connected = True

    def list_tools(self) -> tuple[McpTool, ...]:
        self._ensure_connected()
        if self._cancel.is_set():
            raise McpCancelled("MCP request cancelled")
        return self._tools

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        self._ensure_connected()
        tool = next((item for item in self._tools if item.name == name), None)
        if tool is None:
            raise KeyError(f"unknown MCP tool: {name}")
        if not tool.read_only and not self.config.write_authorized:
            raise PermissionError("MCP server has no approved write permission")
        return self._request("tools/call", {"name": name, "arguments": dict(arguments)})

    def cancel(self) -> None:
        self._cancel.set()
        self.transport.cancel()

    def close(self) -> None:
        self.transport.close()
        self._connected = False

    def _request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        self._ensure_transport()
        last_error: McpTransportError | None = None
        for attempt in range(self.config.max_retries + 1):
            if self._cancel.is_set():
                raise McpCancelled("MCP request cancelled")
            try:
                return self.transport.request(method, params, self._cancel)
            except McpCancelled:
                raise
            except McpTransportError as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    raise
                self.transport.close()
                self.transport.connect(self.config.auth_token)
        raise McpTransportError(str(last_error or "MCP request failed"))

    def _ensure_connected(self) -> None:
        if not self._connected:
            raise McpTransportError("MCP client is not connected")

    def _ensure_transport(self) -> None:
        if self.transport is None:
            raise McpTransportError("MCP transport is missing")

    @staticmethod
    def _map_tools(payload: Mapping[str, Any]) -> tuple[McpTool, ...]:
        raw_tools = payload.get("tools", [])
        if not isinstance(raw_tools, list):
            raise McpTransportError("MCP tools/list result is invalid")
        tools = []
        for raw in raw_tools:
            if not isinstance(raw, dict) or not isinstance(raw.get("name"), str):
                raise McpTransportError("MCP tool schema is invalid")
            schema = raw.get("inputSchema", raw.get("input_schema", {}))
            if not isinstance(schema, dict):
                raise McpTransportError("MCP tool input schema is invalid")
            tools.append(
                McpTool(
                    raw["name"],
                    str(raw.get("description", "")),
                    schema,
                    bool(raw.get("readOnly", raw.get("read_only", False))),
                )
            )
        return tuple(tools)


def _transport_for(config: McpServerConfig) -> McpTransport:
    if config.transport == "stdio":
        return StdioMcpTransport(config.command)
    if config.url is None:
        raise ValueError("streamable HTTP MCP server requires a URL")
    return StreamableHttpMcpTransport(config.url)


def _rpc_result(payload: Any) -> Mapping[str, Any]:
    if not isinstance(payload, dict):
        raise McpTransportError("MCP JSON-RPC response is invalid")
    if payload.get("error") is not None:
        error = payload["error"]
        message = (
            error.get("message", "MCP request failed")
            if isinstance(error, dict)
            else str(error)
        )
        raise McpTransportError(message)
    result = payload.get("result", payload)
    if not isinstance(result, dict):
        raise McpTransportError("MCP JSON-RPC result is invalid")
    return result
