from __future__ import annotations

import argparse
import json
from collections.abc import Iterable

from prompt_optimizer.providers.base import ModelRequest
from prompt_optimizer.providers.offline import OfflineRuleProvider

from .agent import AgentCore, AgentEvent

# RC ID: RC-057. Reuse the same candidate Agent Core event stream in a CLI prototype.


def run(prompt: str) -> Iterable[AgentEvent]:
    return AgentCore(OfflineRuleProvider()).stream(ModelRequest(prompt=prompt))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rabbit Code Agent Core prototype")
    parser.add_argument("prompt")
    args = parser.parse_args(argv)
    for event in run(args.prompt):
        print(json.dumps({"type": event.type.value, "text": event.text}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
