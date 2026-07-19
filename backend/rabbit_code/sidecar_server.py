from __future__ import annotations

import os

from prompt_optimizer.api.app import create_app_server

# RC ID: RC-067. Keep the one-time startup token in the supervisor-to-sidecar environment handoff.

startup_token = os.environ.get("RABBIT_CODE_STARTUP_TOKEN")
if not startup_token:
    raise RuntimeError("RABBIT_CODE_STARTUP_TOKEN is required")

app = create_app_server(
    startup_token=startup_token,
    protocol_version=os.environ.get("RABBIT_CODE_PROTOCOL_VERSION", "v1"),
    strict_boundary=True,
)
