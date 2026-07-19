from __future__ import annotations

import os
import stat
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from prompt_optimizer.identity import DISTRIBUTION_NAME

# RC ID: RC-199. Keep local installation user-scoped and never elevate implicitly.


class InstallPermissionError(RuntimeError):
    """Raised when a user-scoped installation cannot write its selected path."""


@dataclass(frozen=True)
class UserInstallPaths:
    data_dir: Path
    model_root: Path
    user_bin: Path
    user_bin_in_path: bool
    uses_admin: bool = False

    def with_model_root(self, model_root: Path) -> UserInstallPaths:
        return replace(self, model_root=model_root.expanduser().resolve())

    def to_dict(self) -> dict[str, object]:
        return {
            "data_dir": str(self.data_dir),
            "model_root": str(self.model_root),
            "user_bin": str(self.user_bin),
            "user_bin_in_path": self.user_bin_in_path,
            "uses_admin": self.uses_admin,
        }


@dataclass(frozen=True)
class InstallPermissionReport:
    paths: UserInstallPaths
    writable: bool
    elevation_required: bool

    @property
    def data_dir(self) -> Path:
        return self.paths.data_dir

    @property
    def model_root(self) -> Path:
        return self.paths.model_root

    @property
    def user_bin(self) -> Path:
        return self.paths.user_bin

    def to_dict(self) -> dict[str, object]:
        return {
            **self.paths.to_dict(),
            "writable": self.writable,
            "elevation_required": self.elevation_required,
        }


@dataclass(frozen=True)
class ElevationRequest:
    command: str
    reason: str
    alternative: str
    confirmed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "command": self.command,
            "reason": self.reason,
            "alternative": self.alternative,
            "confirmed": self.confirmed,
        }

    def require_confirmation(self) -> None:
        if not self.confirmed:
            raise InstallPermissionError(
                "explicit confirmation is required before any elevated operation"
            )

    def with_confirmation(self, confirmed: bool) -> ElevationRequest:
        return replace(self, confirmed=confirmed)


def user_install_paths(
    *,
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
    windows: bool | None = None,
) -> UserInstallPaths:
    env = environment or os.environ
    home_path = (home or Path.home()).expanduser().resolve()
    is_windows = os.name == "nt" if windows is None else windows
    custom_home = env.get("RABBIT_CODE_HOME")
    if custom_home:
        data_dir = Path(custom_home).expanduser().resolve()
    elif is_windows:
        base = Path(
            env.get("LOCALAPPDATA") or env.get("APPDATA") or home_path / "AppData" / "Local"
        )
        data_dir = (base / DISTRIBUTION_NAME).resolve()
    else:
        base = Path(env.get("XDG_DATA_HOME") or home_path / ".local" / "share")
        data_dir = (base / DISTRIBUTION_NAME).resolve()
    user_bin = (
        Path(env.get("LOCALAPPDATA") or env.get("APPDATA") or home_path / "AppData" / "Local")
        / "bin"
        if is_windows
        else home_path / ".local" / "bin"
    ).expanduser().resolve()
    path_entries = tuple(
        Path(item).expanduser() for item in env.get("PATH", "").split(os.pathsep) if item
    )
    return UserInstallPaths(
        data_dir=data_dir,
        model_root=data_dir / "local-models",
        user_bin=user_bin,
        user_bin_in_path=_path_in_entries(user_bin, path_entries),
    )


def ensure_user_install_paths(paths: UserInstallPaths) -> InstallPermissionReport:
    for name, path in (
        ("application data", paths.data_dir),
        ("model", paths.model_root),
        ("user bin", paths.user_bin),
    ):
        _ensure_writable(path, name)
    return InstallPermissionReport(paths=paths, writable=True, elevation_required=False)


def explicit_elevation_request(*, command: str, reason: str, alternative: str) -> ElevationRequest:
    if not command.strip() or not reason.strip() or not alternative.strip():
        raise InstallPermissionError(
            "elevation request must include command, reason, and alternative"
        )
    return ElevationRequest(command, reason, alternative)


def _ensure_writable(path: Path, label: str) -> None:
    candidate = path.expanduser().resolve()
    parent = candidate
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    if parent.exists() and _has_no_write_bits(parent):
        raise InstallPermissionError(f"{label} directory is not writable; choose a user directory")
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        if _has_no_write_bits(candidate):
            raise InstallPermissionError(
                f"{label} directory is not writable; choose a user directory"
            )
        probe = candidate / f".rabbit-code-permission-{uuid.uuid4().hex}"
        probe.write_bytes(b"")
        probe.unlink()
    except InstallPermissionError:
        raise
    except OSError as exc:
        raise InstallPermissionError(
            f"{label} directory is not writable; choose a user directory"
        ) from exc


def _has_no_write_bits(path: Path) -> bool:
    try:
        return stat.S_IMODE(path.stat().st_mode) & stat.S_IWUSR == 0
    except OSError:
        return True


def _path_in_entries(path: Path, entries: tuple[Path, ...]) -> bool:
    normalized = os.path.normcase(str(path.resolve()))
    return any(
        os.path.normcase(str(entry.expanduser().resolve())) == normalized for entry in entries
    )
