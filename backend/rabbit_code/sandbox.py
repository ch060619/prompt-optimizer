from __future__ import annotations

import ctypes
import os
import platform
import shutil
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

# RC ID: RC-204. Detect and enforce the smallest available cross-platform sandbox.


class SandboxError(PermissionError):
    pass


class SandboxApprovalRequired(SandboxError):
    pass


class SandboxUnavailable(SandboxError):
    pass


class SandboxGuarantee(StrEnum):
    BWRAP = "linux_bwrap"
    JOB_OBJECT = "windows_job_object"
    REDUCED = "reduced"
    WORKSPACE = "workspace_boundary"


@dataclass(frozen=True)
class SandboxCapability:
    name: str
    available: bool
    guarantee: SandboxGuarantee
    detail: str


@dataclass(frozen=True)
class SandboxReport:
    platform: str
    backend: SandboxGuarantee
    capabilities: tuple[SandboxCapability, ...]
    limitations: tuple[str, ...]

    def capability(self, name: str) -> SandboxCapability:
        for capability in self.capabilities:
            if capability.name == name:
                return capability
        raise KeyError(name)

    def to_dict(self) -> dict[str, object]:
        return {
            "platform": self.platform,
            "backend": self.backend.value,
            "capabilities": [
                {
                    "name": capability.name,
                    "available": capability.available,
                    "guarantee": capability.guarantee.value,
                    "detail": capability.detail,
                }
                for capability in self.capabilities
            ],
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class SandboxLaunchSpec:
    command: tuple[str, ...]
    cwd: Path
    env: Mapping[str, str] | None
    guarantee: SandboxGuarantee
    requires_approval: bool
    warning: str | None = None


def detect_sandbox(
    *,
    platform_name: str | None = None,
    executable_finder: Callable[[str], str | None] = shutil.which,
) -> SandboxReport:
    raw_platform = platform_name or platform.system()
    normalized_platform = raw_platform.lower()
    if normalized_platform == "windows":
        job_available = _windows_job_object_available()
        windows_capabilities: tuple[SandboxCapability, ...] = (
            SandboxCapability(
                "job_object",
                job_available,
                SandboxGuarantee.JOB_OBJECT if job_available else SandboxGuarantee.REDUCED,
                "Process trees can be assigned to a Windows Job Object."
                if job_available
                else "Windows Job Object API is unavailable.",
            ),
            SandboxCapability(
                "appcontainer",
                False,
                SandboxGuarantee.REDUCED,
                "AppContainer profile creation is not implemented by this runtime.",
            ),
            SandboxCapability(
                "acl_workspace",
                False,
                SandboxGuarantee.REDUCED,
                "Per-process ACL token setup is not implemented by this runtime.",
            ),
            SandboxCapability(
                "workspace_boundary",
                True,
                SandboxGuarantee.WORKSPACE,
                "Application-level path and symlink boundary is available.",
            ),
        )
        return SandboxReport(
            "windows",
            SandboxGuarantee.JOB_OBJECT if job_available else SandboxGuarantee.WORKSPACE,
            windows_capabilities,
            (
                "AppContainer and ACL controls are not equivalent to the Job Object boundary.",
                "External commands require approval when strong file isolation is unavailable.",
            ),
        )
    if normalized_platform == "linux":
        bwrap = executable_finder("bwrap")
        bwrap_available = bwrap is not None
        linux_capabilities: tuple[SandboxCapability, ...] = (
            SandboxCapability(
                "user_namespace",
                bwrap_available,
                SandboxGuarantee.BWRAP if bwrap_available else SandboxGuarantee.REDUCED,
                "bubblewrap can create a private process and mount namespace."
                if bwrap_available
                else "bubblewrap is not installed.",
            ),
            SandboxCapability(
                "seccomp",
                False,
                SandboxGuarantee.REDUCED,
                "No seccomp profile is installed by this runtime.",
            ),
            SandboxCapability(
                "workspace_boundary",
                True,
                SandboxGuarantee.WORKSPACE,
                "Application-level path and symlink boundary is available.",
            ),
        )
        limitations = (
            "bubblewrap does not provide this runtime with a seccomp policy.",
            "Without bubblewrap, process/mount isolation are unavailable and approval is required.",
        )
        return SandboxReport(
            "linux",
            SandboxGuarantee.BWRAP if bwrap_available else SandboxGuarantee.WORKSPACE,
            linux_capabilities,
            limitations,
        )
    return SandboxReport(
        normalized_platform,
        SandboxGuarantee.WORKSPACE,
        (
            SandboxCapability(
                "workspace_boundary",
                True,
                SandboxGuarantee.WORKSPACE,
                "Application-level path and symlink boundary is available.",
            ),
        ),
        ("No platform process sandbox is registered; reduced execution requires approval.",),
    )


class SandboxController:
    def __init__(
        self,
        workspace_root: Path,
        *,
        report: SandboxReport | None = None,
        require_strong: bool = False,
        network_allowed: bool = False,
    ) -> None:
        self.workspace_root = workspace_root.expanduser().resolve()
        if not self.workspace_root.is_dir():
            raise ValueError("workspace root must be a directory")
        self.report = report or detect_sandbox()
        self.require_strong = require_strong
        self.network_allowed = network_allowed

    def prepare(
        self,
        command: Sequence[str],
        *,
        cwd: str | Path = ".",
        env: Mapping[str, str] | None = None,
        network: bool = False,
        approval: bool = False,
    ) -> SandboxLaunchSpec:
        normalized_command = _command(command)
        working_directory = self._path(cwd, directory=True)
        if network and not self.network_allowed:
            raise SandboxError("network access is disabled by the sandbox profile")
        if self.report.backend is SandboxGuarantee.BWRAP:
            executable = self._bwrap_executable()
            wrapped = [
                executable,
                "--die-with-parent",
                "--unshare-pid",
                "--unshare-uts",
                "--unshare-ipc",
                "--ro-bind",
                str(self.workspace_root),
                str(self.workspace_root),
            ]
            for system_path in ("/bin", "/etc", "/lib", "/lib64", "/usr"):
                if Path(system_path).is_dir():
                    wrapped.extend(("--ro-bind", system_path, system_path))
            wrapped.extend(
                (
                    "--proc",
                    "/proc",
                    "--dev",
                    "/dev",
                    "--tmpfs",
                    "/tmp",
                    "--chdir",
                    str(working_directory),
                )
            )
            if not network:
                wrapped.append("--unshare-net")
            wrapped.extend(("--", *normalized_command))
            return SandboxLaunchSpec(
                tuple(wrapped),
                working_directory,
                env,
                SandboxGuarantee.BWRAP,
                False,
            )
        if self.require_strong:
            raise SandboxUnavailable(
                f"strong sandbox is unavailable on {self.report.platform}: "
                + "; ".join(self.report.limitations)
            )
        if not approval:
            raise SandboxApprovalRequired(
                "platform sandbox is unavailable; explicit approval is required "
                "for reduced execution"
            )
        return SandboxLaunchSpec(
            normalized_command,
            working_directory,
            env,
            SandboxGuarantee.REDUCED,
            True,
            warning=(
                "platform sandbox unavailable; application workspace boundary "
                "and approval are active"
            ),
        )

    def _bwrap_executable(self) -> str:
        executable = shutil.which("bwrap")
        if executable is None:
            raise SandboxUnavailable("bubblewrap is unavailable")
        return executable

    def _path(self, path: str | Path, *, directory: bool) -> Path:
        raw = Path(path).expanduser()
        candidate = raw if raw.is_absolute() else self.workspace_root / raw
        lexical = Path(os.path.abspath(candidate))
        current = self.workspace_root
        try:
            relative = lexical.relative_to(self.workspace_root)
        except ValueError as exc:
            raise SandboxError("path must remain within the workspace") from exc
        for part in relative.parts:
            current /= part
            if current.is_symlink():
                raise SandboxError("symlink paths are not allowed")
        resolved = lexical.resolve(strict=False)
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise SandboxError("path must remain within the workspace") from exc
        if directory and not resolved.is_dir():
            raise FileNotFoundError(resolved)
        return resolved


def _command(command: Sequence[str]) -> tuple[str, ...]:
    if isinstance(command, str) or not command:
        raise TypeError("command must be a non-empty sequence")
    normalized = tuple(str(item) for item in command)
    if any(not item for item in normalized):
        raise ValueError("command arguments must not be empty")
    return normalized


def _windows_job_object_available() -> bool:
    return getattr(ctypes, "windll", None) is not None
