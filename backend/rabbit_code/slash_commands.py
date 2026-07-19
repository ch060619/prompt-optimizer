from __future__ import annotations

import difflib
import shlex
from collections.abc import Callable, Mapping
from dataclasses import dataclass

# RC ID: RC-103. Register, complete, validate, and dispatch slash commands.


class SlashCommandError(ValueError):
    pass


class UnknownSlashCommand(SlashCommandError):
    pass


class SlashArgumentError(SlashCommandError):
    pass


@dataclass(frozen=True)
class SlashArgument:
    name: str
    required: bool = False
    description: str = ""


@dataclass(frozen=True)
class SlashInvocation:
    name: str
    arguments: tuple[str, ...]


@dataclass(frozen=True)
class SlashResult:
    command: str
    output: str
    affects_session: bool
    exit_requested: bool = False


SlashHandler = Callable[[SlashInvocation], SlashResult]


@dataclass(frozen=True)
class SlashCommandSpec:
    name: str
    description: str
    arguments: tuple[SlashArgument, ...] = ()
    affects_session: bool = False
    handler: SlashHandler | None = None

    def __post_init__(self) -> None:
        if not self.name or self.name.startswith("/") or " " in self.name:
            raise SlashCommandError("slash command name must be a single token")
        if not self.description.strip():
            raise SlashCommandError("slash command description is required")


class SlashCommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, SlashCommandSpec] = {}

    def register(self, spec: SlashCommandSpec) -> SlashCommandSpec:
        if spec.name in self._commands:
            raise SlashCommandError(f"slash command is already registered: /{spec.name}")
        self._commands[spec.name] = spec
        return spec

    def get(self, name: str) -> SlashCommandSpec:
        try:
            return self._commands[name.removeprefix("/")]
        except KeyError as exc:
            suggestion = difflib.get_close_matches(name.removeprefix("/"), self._commands, n=1)
            hint = f"; did you mean /{suggestion[0]}" if suggestion else ""
            message = f"unknown slash command: /{name.removeprefix('/')}" + hint
            raise UnknownSlashCommand(message) from exc

    def complete(self, prefix: str) -> tuple[str, ...]:
        normalized = prefix.removeprefix("/")
        return tuple(f"/{name}" for name in sorted(self._commands) if name.startswith(normalized))

    def help(self) -> str:
        lines = ["Slash commands:"]
        for name in sorted(self._commands):
            spec = self._commands[name]
            args = " ".join(
                f"<{argument.name}>" if argument.required else f"[{argument.name}]"
                for argument in spec.arguments
            )
            suffix = f" {args}" if args else ""
            scope = " session" if spec.affects_session else ""
            lines.append(f"/{name}{suffix} - {spec.description}{scope}")
        return "\n".join(lines)

    def parse(self, text: str) -> SlashInvocation:
        if not isinstance(text, str) or not text.startswith("/"):
            raise SlashCommandError("slash command must start with /")
        try:
            tokens = shlex.split(text)
        except ValueError as exc:
            raise SlashArgumentError(f"invalid slash command quoting: {exc}") from exc
        if not tokens:
            raise SlashCommandError("slash command is empty")
        spec = self.get(tokens[0])
        arguments = tuple(tokens[1:])
        required = sum(argument.required for argument in spec.arguments)
        if len(arguments) < required:
            raise SlashArgumentError(f"/{spec.name} requires {required} argument(s)")
        if len(arguments) > len(spec.arguments):
            raise SlashArgumentError(
                f"/{spec.name} accepts at most {len(spec.arguments)} argument(s)"
            )
        return SlashInvocation(spec.name, arguments)

    def dispatch(self, text: str) -> SlashResult:
        invocation = self.parse(text)
        spec = self.get(invocation.name)
        if spec.handler is not None:
            return spec.handler(invocation)
        return SlashResult(
            command=invocation.name,
            output="",
            affects_session=spec.affects_session,
            exit_requested=invocation.name == "exit",
        )


def default_slash_registry() -> SlashCommandRegistry:
    registry = SlashCommandRegistry()
    commands: Mapping[str, tuple[str, tuple[SlashArgument, ...], bool]] = {
        "help": ("Show registered slash commands", (), False),
        "model": (
            "Select or inspect the model",
            (SlashArgument("model", required=True),),
            True,
        ),
        "provider": (
            "Select or inspect the provider",
            (SlashArgument("provider", required=True),),
            True,
        ),
        "permission": (
            "Inspect or change permission mode",
            (SlashArgument("mode", required=True),),
            True,
        ),
        "plan": ("Inspect the current plan", (), True),
        "context": ("Inspect the current context", (), True),
        "session": (
            "Inspect or switch the session",
            (SlashArgument("session", required=True),),
            True,
        ),
        "clear": ("Clear the current draft or view", (), True),
        "compact": ("Compact current context", (), True),
        "mcp": ("Inspect MCP tools", (), True),
        "plugin": ("Inspect plugins", (), True),
        "doctor": ("Run diagnostics", (), False),
        "exit": ("Exit the interactive session", (), False),
    }
    for name, (description, arguments, affects_session) in commands.items():
        registry.register(
            SlashCommandSpec(
                name=name,
                description=description,
                arguments=arguments,
                affects_session=affects_session,
                handler=_default_handler if name not in {"help"} else _help_handler(registry),
            )
        )
    return registry


def _help_handler(registry: SlashCommandRegistry) -> SlashHandler:
    def handle(invocation: SlashInvocation) -> SlashResult:
        return SlashResult(invocation.name, registry.help(), False)

    return handle


def _default_handler(invocation: SlashInvocation) -> SlashResult:
    return SlashResult(
        command=invocation.name,
        output=" ".join(invocation.arguments),
        affects_session=invocation.name
        not in {"help", "doctor", "exit"},
        exit_requested=invocation.name == "exit",
    )
