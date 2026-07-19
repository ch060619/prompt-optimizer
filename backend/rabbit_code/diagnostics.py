from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

# RC ID: RC-093. Normalize common development tool diagnostics for CLI and GUI consumers.


class DiagnosticSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    NOTE = "note"


@dataclass(frozen=True)
class Diagnostic:
    file: Path | None
    line: int | None
    column: int | None
    severity: DiagnosticSeverity
    message: str
    command: tuple[str, ...]
    source: str
    raw: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["file"] = self.file.as_posix() if self.file is not None else None
        payload["severity"] = self.severity.value
        payload["command"] = list(self.command)
        return payload


@dataclass(frozen=True)
class DiagnosticReport:
    command: tuple[str, ...]
    exit_code: int
    diagnostics: tuple[Diagnostic, ...]
    stdout: str
    stderr: str
    parse_failed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": list(self.command),
            "exit_code": self.exit_code,
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
            "stdout": self.stdout,
            "stderr": self.stderr,
            "parse_failed": self.parse_failed,
        }


class DiagnosticParser:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.expanduser().resolve()

    def parse(
        self,
        command: tuple[str, ...],
        *,
        stdout: str,
        stderr: str,
        exit_code: int,
        source: str | None = None,
    ) -> DiagnosticReport:
        if not command:
            raise ValueError("command must be non-empty")
        normalized_command = tuple(command)
        tool = source or _tool_name(command[0])
        diagnostics: list[Diagnostic] = []
        raw_output = "\n".join(part for part in (stdout, stderr) if part)
        for raw_line in raw_output.splitlines():
            diagnostic = self._parse_line(raw_line, normalized_command, tool)
            if diagnostic is not None:
                diagnostics.append(diagnostic)
        parse_failed = bool(raw_output) and not diagnostics
        if exit_code != 0 and not diagnostics:
            diagnostics.append(
                Diagnostic(
                    file=None,
                    line=None,
                    column=None,
                    severity=DiagnosticSeverity.ERROR,
                    message="command failed; raw output preserved",
                    command=normalized_command,
                    source=tool,
                    raw=raw_output,
                )
            )
        return DiagnosticReport(
            normalized_command,
            exit_code,
            tuple(diagnostics),
            stdout,
            stderr,
            parse_failed,
        )

    def _parse_line(
        self,
        raw_line: str,
        command: tuple[str, ...],
        source: str,
    ) -> Diagnostic | None:
        line = raw_line.strip()
        match = _RUFF_PATTERN.match(line)
        if match:
            code = match.group("code")
            severity = (
                DiagnosticSeverity.ERROR
                if code[0] in {"E", "F"}
                else DiagnosticSeverity.WARNING
            )
            return self._diagnostic(
                match.group("file"),
                match.group("line"),
                match.group("column"),
                severity,
                f"{code} {match.group('message')}",
                command,
                source,
                raw_line,
            )
        match = _MYPY_PATTERN.match(line)
        if match:
            return self._diagnostic(
                match.group("file"),
                match.group("line"),
                match.group("column"),
                DiagnosticSeverity(match.group("severity")),
                match.group("message"),
                command,
                source,
                raw_line,
            )
        match = _TSC_PATTERN.match(line)
        if match:
            return self._diagnostic(
                match.group("file"),
                match.group("line"),
                match.group("column"),
                DiagnosticSeverity(match.group("severity")),
                match.group("message"),
                command,
                source,
                raw_line,
            )
        match = _PYTEST_PATTERN.match(line)
        if match:
            return Diagnostic(
                file=self._normalize_file(match.group("file")),
                line=None,
                column=None,
                severity=DiagnosticSeverity.ERROR,
                message=match.group("message"),
                command=command,
                source=source,
                raw=raw_line,
            )
        return None

    def _diagnostic(
        self,
        raw_file: str,
        raw_line: str,
        raw_column: str | None,
        severity: DiagnosticSeverity,
        message: str,
        command: tuple[str, ...],
        source: str,
        raw: str,
    ) -> Diagnostic:
        return Diagnostic(
            file=self._normalize_file(raw_file),
            line=int(raw_line),
            column=int(raw_column) if raw_column is not None else None,
            severity=severity,
            message=message,
            command=command,
            source=source,
            raw=raw,
        )

    def _normalize_file(self, raw_file: str) -> Path:
        candidate = Path(raw_file)
        if not candidate.is_absolute():
            candidate = self.workspace_root / candidate
        resolved = candidate.resolve()
        try:
            return resolved.relative_to(self.workspace_root)
        except ValueError:
            return Path(raw_file)


_RUFF_PATTERN = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+):(?P<column>\d+):\s+(?P<code>[A-Z]\d+)\s+(?P<message>.+)$"
)
_MYPY_PATTERN = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+)(?::(?P<column>\d+))?:\s+"
    r"(?P<severity>error|warning|note|info):\s+(?P<message>.+)$"
)
_TSC_PATTERN = re.compile(
    r"^(?P<file>.+?)\((?P<line>\d+),(?P<column>\d+)\):\s+"
    r"(?P<severity>error|warning)\s+(?P<message>.+)$"
)
_PYTEST_PATTERN = re.compile(
    r"^(?:FAILED|ERROR)\s+(?P<file>[^:]+)(?:::.+)?(?::\s*(?P<message>.*))?$"
)


def _tool_name(executable: str) -> str:
    return Path(executable).name.casefold()
