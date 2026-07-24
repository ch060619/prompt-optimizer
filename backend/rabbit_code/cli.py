from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Literal, TextIO, cast

from prompt_optimizer.providers.base import ModelRequest
from prompt_optimizer.providers.offline import OfflineRuleProvider

from .agent import AgentEvent, AgentEventType
from .ci_execution import NonInteractiveError, resolve_non_interactive_policy
from .dry_run import DryRunPlanner, LogLevel, MachineEventStream, MachineEventType
from .runtime import AgentRuntime, AppServerRuntime, InProcessRuntime
from .tui import TuiRenderer, TuiSession

# RC ID: RC-057. Reuse the same candidate Agent Core event stream in a CLI prototype.
# RC ID: RC-069. Support interactive, one-shot, piped, text, JSON, and JSONL execution modes.

OutputMode = Literal["text", "json", "jsonl"]
CliCommand = Literal["run", "continue", "resume", "model", "mode", "output", "tui"]
CLI_COMMANDS = frozenset({"run", "continue", "resume", "model", "mode", "output", "tui"})
CLI_MODES = frozenset({"plan", "edit", "high"})
EXIT_OK = 0
EXIT_RUNTIME_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_PERMISSION_DENIED = 3
EXIT_CANCELLED = 130


def run(prompt: str, runtime: AgentRuntime | None = None) -> Iterable[AgentEvent]:
    selected_runtime = runtime or InProcessRuntime(OfflineRuleProvider())
    return selected_runtime.stream(ModelRequest(prompt=prompt))


def main(
    argv: list[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    runtime: AgentRuntime | None = None,
) -> int:
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    error_stream = stderr or sys.stderr
    raw_args = list(argv if argv is not None else sys.argv[1:])
    command = cast(
        CliCommand,
        raw_args.pop(0) if raw_args and raw_args[0] in CLI_COMMANDS else "run",
    )
    parser = argparse.ArgumentParser(
        prog="rabbit",
        description="Rabbit Code Agent Core",
        epilog=(
            "commands: run, continue, resume, model, mode, output; "
            "tui; run/continue/resume/tui consume a prompt or stdin"
        ),
    )
    parser.add_argument("values", nargs="*", metavar="VALUE")
    parser.add_argument("--output", choices=("text", "json", "jsonl"), default=None)
    parser.add_argument("--runtime", choices=("in-process", "app-server"), default="in-process")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--startup-token", default="")
    parser.add_argument("--session", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--mode", choices=tuple(sorted(CLI_MODES)), default=None)
    parser.add_argument("--width", type=int, default=80)
    parser.add_argument("--height", type=int, default=24)
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument(
        "--permission-policy",
        choices=("deny", "read-only", "approve"),
        default=None,
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--read-only", action="store_true")
    parser.add_argument(
        "--log-level",
        choices=tuple(item.value for item in LogLevel),
        default="info",
    )
    args = parser.parse_args(raw_args)
    if args.read_only and args.permission_policy == "approve":
        error_stream.write("error: --read-only conflicts with --permission-policy approve\n")
        return EXIT_USAGE_ERROR
    try:
        resolve_non_interactive_policy(
            stdin_is_tty=input_stream.isatty(),
            force_non_interactive=args.non_interactive,
            requested=args.permission_policy,
        )
    except NonInteractiveError as exc:
        error_stream.write(f"error: {exc}\n")
        return EXIT_USAGE_ERROR
    output_mode: OutputMode = args.output or ("text" if input_stream.isatty() else "jsonl")
    if command in {"model", "mode", "output"}:
        return _control_command(command, args.values, output_mode, output_stream, error_stream)
    if command in {"continue", "resume"}:
        if args.session is None and not args.values:
            error_stream.write(f"error: {command} requires a session id\n")
            return EXIT_USAGE_ERROR
        prompt_arg = (
            args.values[0]
            if args.session is not None
            else args.values[1]
            if len(args.values) > 1
            else None
        )
    else:
        prompt_arg = args.values[0] if args.values else None
    selected_runtime = runtime
    if args.runtime == "app-server":
        if not args.startup_token:
            error_stream.write("error: --runtime app-server requires --startup-token\n")
            return EXIT_USAGE_ERROR
        selected_runtime = AppServerRuntime(args.base_url, args.startup_token)
    if selected_runtime is None:
        selected_runtime = InProcessRuntime(OfflineRuleProvider())
    prompts = _read_prompts(
        prompt_arg,
        input_stream,
        output_stream,
        output_mode,
        force_non_interactive=args.non_interactive,
    )
    if not prompts:
        error_stream.write("error: prompt is required or must be provided on stdin\n")
        return EXIT_USAGE_ERROR
    if args.dry_run:
        return _emit_dry_run(
            prompts,
            output_mode,
            output_stream,
            permission=(
                "read-only"
                if args.read_only
                else args.permission_policy or "read-only"
            ),
            log_level=args.log_level,
        )
    if command == "tui":
        try:
            state = TuiSession(selected_runtime).submit(prompts[0])
            rendered = TuiRenderer.render(state, width=args.width, height=args.height)
            artwork = TuiRenderer.inline_artwork()
            if artwork:
                output_stream.write(artwork + "\n")
            output_stream.write(rendered + "\n")
            output_stream.flush()
        except ValueError as exc:
            error_stream.write(f"error: {exc}\n")
            return EXIT_USAGE_ERROR
        return EXIT_OK
    for prompt in prompts:
        exit_code = execute(prompt, selected_runtime, output_mode, output_stream, error_stream)
        if exit_code != EXIT_OK:
            return exit_code
    return EXIT_OK


def _emit_dry_run(
    prompts: list[str],
    output_mode: OutputMode,
    stdout: TextIO,
    *,
    permission: str,
    log_level: str,
) -> int:
    stream = MachineEventStream()
    planner = DryRunPlanner()
    for prompt in prompts:
        action = planner.plan(("rabbit", "run", prompt), cwd=Path.cwd(), permission=permission)
        stream.emit(
            MachineEventType.DRY_RUN,
            {"action": action.to_dict(), "log_level": log_level},
        )
    if output_mode == "json":
        stdout.write(json.dumps(stream.json(), ensure_ascii=False) + "\n")
    elif output_mode == "jsonl":
        stdout.write(stream.jsonl())
    else:
        for event in stream.events:
            stdout.write(
                f"dry-run: {event.payload['action']['command']} "
                f"permission={event.payload['action']['permission']}\n"
            )
    stdout.flush()
    return EXIT_OK


def _control_command(
    command: CliCommand,
    values: list[str],
    output_mode: OutputMode,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    if len(values) != 1:
        stderr.write(f"error: {command} requires exactly one value\n")
        return EXIT_USAGE_ERROR
    value = values[0]
    if command == "mode" and value not in CLI_MODES:
        stderr.write(f"error: mode must be one of {', '.join(sorted(CLI_MODES))}\n")
        return EXIT_USAGE_ERROR
    payload = {"command": command, "value": value}
    if output_mode == "json":
        stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    elif output_mode == "jsonl":
        stdout.write(json.dumps({"type": command, **payload}, ensure_ascii=False) + "\n")
    else:
        stdout.write(value + "\n")
    stdout.flush()
    return EXIT_OK


def execute(
    prompt: str,
    runtime: AgentRuntime,
    output_mode: OutputMode,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        events = list(run(prompt, runtime))
    except KeyboardInterrupt:
        stderr.write("cancelled\n")
        return EXIT_CANCELLED
    except PermissionError as exc:
        stderr.write(f"permission denied: {exc}\n")
        return EXIT_PERMISSION_DENIED
    except Exception as exc:
        stderr.write(f"error: {exc}\n")
        return EXIT_RUNTIME_ERROR
    payloads = [
        {
            "type": event.type.value,
            "text": event.text,
            "seq": event.sequence,
            "payload": dict(event.payload),
        }
        for event in events
    ]
    if output_mode == "jsonl":
        for payload in payloads:
            stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    elif output_mode == "json":
        stdout.write(json.dumps({"events": payloads}, ensure_ascii=False) + "\n")
    else:
        text = "".join(
            event.text or "" for event in events if event.type is AgentEventType.DELTA
        )
        stdout.write(text)
        if events and events[-1].type is AgentEventType.COMPLETED:
            stdout.write("\n")
    stdout.flush()
    if events and events[-1].type is AgentEventType.CANCELLED:
        return EXIT_CANCELLED
    if events and events[-1].type is AgentEventType.FAILED:
        return EXIT_RUNTIME_ERROR
    return EXIT_OK


def _read_prompts(
    prompt: str | None,
    stdin: TextIO,
    stdout: TextIO,
    output_mode: OutputMode,
    *,
    force_non_interactive: bool = False,
) -> list[str]:
    if prompt is not None and prompt.strip():
        return [prompt]
    if not force_non_interactive and stdin.isatty() and output_mode == "text":
        stdout.write("rabbit> ")
        stdout.flush()
        line = stdin.readline()
        return [line.strip()] if line.strip() else []
    content = stdin.read().strip()
    return [content] if content else []


if __name__ == "__main__":
    raise SystemExit(main())
