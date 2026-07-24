"""Minimal stdio JSON-RPC MCP-shaped example with one read-only tool."""

from __future__ import annotations

import json
import sys


def respond(request: dict[str, object]) -> dict[str, object]:
    method = request.get("method")
    request_id = request.get("id")
    if method == "initialize":
        result = {"protocolVersion": "v1", "capabilities": {"tools": {}}}
    elif method == "tools/list":
        result = {
            "tools": [
                {
                    "name": "example_status",
                    "description": "Return a static local status.",
                    "inputSchema": {"type": "object", "properties": {}},
                    "readOnly": True,
                }
            ]
        }
    elif method == "tools/call":
        params = request.get("params")
        if not isinstance(params, dict) or params.get("name") != "example_status":
            return {"jsonrpc": "2.0", "id": request_id, "error": {"message": "unknown tool"}}
        result = {"content": [{"type": "text", "text": "ready"}]}
    else:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"message": "unknown method"}}
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def run_stdio() -> None:
    for line in sys.stdin:
        if line.strip():
            print(json.dumps(respond(json.loads(line)), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    run_stdio()
