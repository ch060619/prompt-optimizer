from __future__ import annotations

import argparse
import json
from collections.abc import Iterable

from prompt_optimizer.providers.base import ModelRequest
from prompt_optimizer.providers.offline import OfflineRuleProvider

from .agent import AgentEvent
from .runtime import AgentRuntime, AppServerRuntime, InProcessRuntime

# RC ID: RC-057. Reuse the same candidate Agent Core event stream in a CLI prototype.


def run(prompt: str, runtime: AgentRuntime | None = None) -> Iterable[AgentEvent]:
    selected_runtime = runtime or InProcessRuntime(OfflineRuleProvider())
    return selected_runtime.stream(ModelRequest(prompt=prompt))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rabbit Code Agent Core prototype")
    parser.add_argument("prompt")
    parser.add_argument("--runtime", choices=("in-process", "app-server"), default="in-process")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--startup-token", default="")
    args = parser.parse_args(argv)
    runtime: AgentRuntime | None = None
    if args.runtime == "app-server":
        if not args.startup_token:
            parser.error("--runtime app-server requires --startup-token")
        runtime = AppServerRuntime(args.base_url, args.startup_token)
    for event in run(args.prompt, runtime):
        print(json.dumps({"type": event.type.value, "text": event.text}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
