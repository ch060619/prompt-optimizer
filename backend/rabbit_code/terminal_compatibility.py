from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from enum import StrEnum

# RC ID: RC-107. Describe terminal availability without claiming unavailable TTY features.


class TerminalKind(StrEnum):
    WINDOWS_TERMINAL = "windows-terminal"
    POWERSHELL = "powershell"
    CMD = "cmd"
    WSL = "wsl"
    LINUX = "linux"


@dataclass(frozen=True)
class TerminalCapability:
    kind: TerminalKind
    available: bool
    executable: str | None
    interactive: bool
    reason: str


def detect_terminal_matrix() -> tuple[TerminalCapability, ...]:
    windows_terminal = shutil.which("wt")
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    cmd = shutil.which("cmd.exe") or shutil.which("cmd")
    wsl = shutil.which("wsl")
    native_linux = sys.platform.startswith("linux")
    return (
        TerminalCapability(
            TerminalKind.WINDOWS_TERMINAL,
            windows_terminal is not None,
            windows_terminal,
            bool(os.environ.get("WT_SESSION")),
            "interactive Windows Terminal session detected"
            if os.environ.get("WT_SESSION")
            else "Windows Terminal executable is available but WT_SESSION is absent",
        ),
        TerminalCapability(
            TerminalKind.POWERSHELL,
            powershell is not None,
            powershell,
            bool(sys.stdin.isatty() and sys.stdout.isatty()),
            "PowerShell executable detected"
            if powershell
            else "PowerShell executable is unavailable",
        ),
        TerminalCapability(
            TerminalKind.CMD,
            cmd is not None,
            cmd,
            bool(sys.stdin.isatty() and sys.stdout.isatty()),
            "cmd executable detected" if cmd else "cmd executable is unavailable",
        ),
        TerminalCapability(
            TerminalKind.WSL,
            wsl is not None,
            wsl,
            bool(os.environ.get("WSL_INTEROP")),
            "WSL executable detected" if wsl else "WSL executable is unavailable",
        ),
        TerminalCapability(
            TerminalKind.LINUX,
            native_linux,
            shutil.which("sh") if native_linux else None,
            bool(sys.stdin.isatty() and sys.stdout.isatty()) if native_linux else False,
            "native Linux host detected"
            if native_linux
            else "native Linux terminal is unavailable on this Windows host",
        ),
    )


def clipboard_status() -> tuple[bool, str]:
    if sys.platform.startswith("linux"):
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            return True, "desktop clipboard session detected"
        return False, "Linux clipboard requires DISPLAY or WAYLAND_DISPLAY"
    if os.name == "nt":
        if os.environ.get("WT_SESSION"):
            return True, "interactive Windows Terminal clipboard session detected"
        return False, "clipboard requires an interactive Windows Terminal session"
    return False, "clipboard integration is unsupported on this platform"
