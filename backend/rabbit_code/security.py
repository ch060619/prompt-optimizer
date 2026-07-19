from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

# RC ID: RC-205. Keep paths, argv, environment, and tool output explicitly untrusted.


class SecurityRisk(StrEnum):
    SAFE = "safe"
    SHELL_SYNTAX = "shell_syntax"
    PRIVILEGED = "privileged"


class EnvironmentVariableDenied(PermissionError):
    pass


class UntrustedPathError(PermissionError):
    pass


_SHELL_MARKERS = re.compile(r"(?:[;&|<>`$]|\$\(|\$\{|\n|\r)")
_OVERRIDE_MARKERS = re.compile(
    r"(?:ignore\s+(?:all\s+)?previous\s+instructions|system\s+prompt|"
    r"grant\s+(?:full\s+)?permission|disable\s+(?:all\s+)?safety|"
    r"you\s+are\s+now)",
    re.IGNORECASE,
)
_ALLOWED_ENV_NAMES = frozenset(
    {
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "HOME",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "PYTHONUTF8",
        "PYTHONIOENCODING",
    }
)
_DANGEROUS_ENV_NAMES = frozenset(
    {
        "LD_PRELOAD",
        "LD_LIBRARY_PATH",
        "DYLD_INSERT_LIBRARIES",
        "DYLD_LIBRARY_PATH",
        "PYTHONPATH",
        "PYTHONINSPECT",
        "PYTHONSTARTUP",
        "NODE_OPTIONS",
        "RUBYOPT",
        "PERL5OPT",
        "GIT_CONFIG_PARAMETERS",
        "GIT_EXTERNAL_DIFF",
    }
)


def normalize_workspace_path(workspace_root: Path, path: str | Path) -> Path:
    root = workspace_root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError("workspace root must be a directory")
    raw = Path(path).expanduser()
    candidate = raw if raw.is_absolute() else root / raw
    lexical = Path(os.path.abspath(candidate))
    try:
        relative = lexical.relative_to(root)
    except ValueError as exc:
        raise UntrustedPathError("path must remain within the workspace") from exc
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise UntrustedPathError("symlink paths are not allowed")
    resolved = lexical.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise UntrustedPathError("path must remain within the workspace") from exc
    return resolved


def validate_argv(args: Sequence[str]) -> tuple[str, ...]:
    if isinstance(args, str) or not args:
        raise TypeError("command arguments must be a non-empty sequence")
    normalized = tuple(str(arg) for arg in args)
    if any(not arg for arg in normalized):
        raise ValueError("command arguments must not be empty")
    if any("\x00" in arg for arg in normalized):
        raise ValueError("command arguments must not contain NUL")
    return normalized


def classify_command(args: Sequence[str]) -> SecurityRisk:
    normalized = validate_argv(args)
    if any(_SHELL_MARKERS.search(item) for item in normalized):
        return SecurityRisk.SHELL_SYNTAX
    return SecurityRisk.SAFE


def sanitize_environment(
    values: Mapping[str, str],
    *,
    reject_unknown: bool = True,
) -> dict[str, str]:
    sanitized: dict[str, str] = {}
    for raw_name, raw_value in values.items():
        name = str(raw_name)
        allowed = (
            name in _ALLOWED_ENV_NAMES
            or name.startswith("LC_")
            or name.startswith("RC_")
            or name.startswith("RABBIT_CODE_")
        )
        if name in _DANGEROUS_ENV_NAMES or not allowed:
            if reject_unknown:
                raise EnvironmentVariableDenied(f"environment variable is not allowlisted: {name}")
            continue
        sanitized[name] = str(raw_value)
    return sanitized


@dataclass(frozen=True)
class UntrustedToolOutput:
    source: str
    text: str
    trusted: bool = False

    @property
    def contains_instruction_override(self) -> bool:
        return bool(_OVERRIDE_MARKERS.search(self.text))

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "text": self.text,
            "trusted": False,
            "can_execute": False,
            "contains_instruction_override": self.contains_instruction_override,
            "sha256": self.digest,
        }
