from __future__ import annotations

import ctypes
import json
import os
import platform
import socket
import subprocess
import urllib.parse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from shutil import disk_usage, which
from typing import Literal

# RC ID: RC-186. Report hardware capability without making detection a hard dependency.

Confidence = Literal["high", "medium", "low", "user"]
CommandRunner = Callable[[Sequence[str]], tuple[int, str, str]]
FileReader = Callable[[Path], str]
WhichReader = Callable[[str], str | None]
NetworkProbe = Callable[[], bool]


@dataclass(frozen=True)
class DiskUsage:
    total: int
    used: int
    free: int


@dataclass(frozen=True)
class HardwareField:
    value: object
    source: str
    confidence: Confidence

    def to_dict(self) -> dict[str, object]:
        return {
            "confidence": self.confidence,
            "source": self.source,
            "value": self.value,
        }


@dataclass(frozen=True)
class HardwareReport:
    fields: Mapping[str, HardwareField]

    def to_dict(self) -> dict[str, object]:
        return {
            "fields": {
                name: self.fields[name].to_dict() for name in sorted(self.fields)
            },
            "schema_version": 1,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)


class HardwareDetector:
    def __init__(
        self,
        *,
        root: Path | None = None,
        command_runner: CommandRunner | None = None,
        file_reader: FileReader | None = None,
        which_reader: WhichReader | None = None,
        network_probe: NetworkProbe | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self.root = root or Path.cwd()
        self._command_runner = command_runner or _run_command
        self._file_reader = file_reader or _read_text
        self._which_reader = which_reader or which
        self._network_probe = network_probe or _probe_network
        self._environment = environment or os.environ

    def detect(self, overrides: Mapping[str, object] | None = None) -> HardwareReport:
        fields: dict[str, HardwareField] = {
            "architecture": self._field(platform.machine() or None, "platform", "high"),
            "cpu": self._cpu(),
            "disk": self._disk(),
            "gpu": self._gpu(),
            "network": self._network(),
            "os": self._field(self._os(), "platform", "high"),
            "proxy": self._field(self._proxy(), "environment", "medium"),
            "ram": self._ram(),
            "runners": self._field(self._runners(), "PATH", "medium"),
        }
        for name, value in (overrides or {}).items():
            if name in fields:
                fields[name] = HardwareField(value=value, source="user", confidence="user")
        return HardwareReport(fields)

    def _field(self, value: object, source: str, confidence: Confidence) -> HardwareField:
        return HardwareField(value=value, source=source, confidence=confidence)

    @staticmethod
    def _os() -> dict[str, str | None]:
        return {
            "name": platform.system() or None,
            "release": platform.release() or None,
        }

    def _cpu(self) -> HardwareField:
        model = platform.processor() or None
        if not model:
            model = self._procfs_value("model name") or self._procfs_value("Hardware")
        value = {"logical_cores": os.cpu_count(), "model": model}
        confidence: Confidence = "high" if model or value["logical_cores"] else "low"
        return self._field(value, "platform/procfs", confidence)

    def _ram(self) -> HardwareField:
        total = self._procfs_memory()
        if total is None and os.name == "nt":
            total = _windows_memory()
        return self._field(
            {"total_bytes": total},
            "procfs/platform",
            "high" if total is not None else "low",
        )

    def _disk(self) -> HardwareField:
        try:
            usage = _read_disk_usage(self.root)
            value = {
                "path": str(self.root),
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
            }
            return self._field(value, "filesystem", "high")
        except (OSError, PermissionError):
            return self._field(
                {
                    "path": str(self.root),
                    "total_bytes": None,
                    "used_bytes": None,
                    "free_bytes": None,
                },
                "filesystem",
                "low",
            )

    def _gpu(self) -> HardwareField:
        for executable, arguments in (
            (
                "nvidia-smi",
                ("--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"),
            ),
            (
                "rocm-smi",
                ("--showproductname", "--showmeminfo", "vram", "--showdriverversion", "--csv"),
            ),
        ):
            path = self._which(executable)
            if not path:
                continue
            try:
                code, stdout, _ = self._command_runner((path, *arguments))
            except (OSError, TimeoutError):
                continue
            if code == 0:
                devices = [
                    self._parse_gpu_line(line) for line in stdout.splitlines() if line.strip()
                ]
                return self._field(
                    {"devices": devices, "detected": bool(devices)},
                    "command",
                    "high" if devices else "low",
                )
        return self._field({"devices": [], "detected": False}, "gpu probe", "low")

    @staticmethod
    def _parse_gpu_line(line: str) -> dict[str, object]:
        parts = [part.strip() for part in line.split(",")]
        return {
            "name": parts[0] if parts and parts[0] else None,
            "memory_mb": _parse_int(parts[1]) if len(parts) > 1 else None,
            "driver": parts[2] if len(parts) > 2 and parts[2] else None,
        }

    def _network(self) -> HardwareField:
        try:
            resolved = bool(self._network_probe())
        except (OSError, TimeoutError):
            resolved = False
        return self._field(
            {"dns_resolution": resolved},
            "socket",
            "high" if resolved else "low",
        )

    def _proxy(self) -> dict[str, object]:
        entries: list[dict[str, str]] = []
        for name in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY"):
            value = self._environment.get(name)
            if value:
                entries.append({"name": name.lower(), "endpoint": _redact_proxy(value)})
        no_proxy = self._environment.get("NO_PROXY", "")
        return {
            "configured": bool(entries),
            "entries": entries,
            "no_proxy": [item for item in no_proxy.split(",") if item],
        }

    def _runners(self) -> dict[str, object]:
        candidates = {
            "ollama": ("ollama", ("--version",)),
            "llama-cpp": ("llama-server", ("--version",)),
        }
        result: dict[str, object] = {}
        for name, (executable, arguments) in candidates.items():
            path = self._which(executable)
            version = None
            if path:
                try:
                    code, stdout, _ = self._command_runner((path, *arguments))
                    if code == 0:
                        version = stdout.strip().splitlines()[0] if stdout.strip() else None
                except (OSError, TimeoutError):
                    pass
            result[name] = {"installed": path is not None, "path": path, "version": version}
        return result

    def _procfs_value(self, key: str) -> str | None:
        try:
            content = self._file_reader(Path("/proc/cpuinfo"))
        except (OSError, PermissionError):
            return None
        prefix = f"{key}:"
        for line in content.splitlines():
            if line.startswith(prefix):
                return line.partition(":")[2].strip() or None
        return None

    def _which(self, executable: str) -> str | None:
        try:
            return self._which_reader(executable)
        except OSError:
            return None

    def _procfs_memory(self) -> int | None:
        try:
            content = self._file_reader(Path("/proc/meminfo"))
        except (OSError, PermissionError):
            return None
        for line in content.splitlines():
            key, separator, remainder = line.partition(":")
            if separator and key == "MemTotal":
                parts = remainder.strip().split()
                if parts:
                    value = _parse_int(parts[0])
                    if value is not None:
                        return value * (1024 if len(parts) > 1 and parts[1] == "kB" else 1)
        return None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_disk_usage(path: Path) -> DiskUsage:
    usage = disk_usage(path)
    return DiskUsage(total=usage.total, used=usage.used, free=usage.free)


def _run_command(arguments: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        list(arguments),
        capture_output=True,
        check=False,
        text=True,
        timeout=2,
    )
    return completed.returncode, completed.stdout, completed.stderr


def _probe_network() -> bool:
    socket.getaddrinfo("example.com", 443, type=socket.SOCK_STREAM)
    return True


def _parse_int(value: str) -> int | None:
    try:
        return int(float(value.strip()))
    except (TypeError, ValueError):
        return None


def _redact_proxy(value: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(value)
        if not parsed.hostname:
            return "configured"
        host = parsed.hostname
        if ":" in host:
            host = f"[{host}]"
        port = f":{parsed.port}" if parsed.port else ""
        return f"{parsed.scheme or 'proxy'}://{host}{port}"
    except ValueError:
        return "configured"


def _windows_memory() -> int | None:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_ulong),
            ("memory_load", ctypes.c_ulong),
            ("total_physical", ctypes.c_ulonglong),
            ("available_physical", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong),
            ("available_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong),
            ("available_virtual", ctypes.c_ulonglong),
            ("available_extended_virtual", ctypes.c_ulonglong),
        ]

    try:
        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)) == 0:
            return None
        return int(status.total_physical)
    except (AttributeError, OSError):
        return None
