from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum

# RC ID: RC-096. Classify tool completion and bound captured output.


class ToolOutcome(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class OutputMetadata:
    bytes_seen: int
    sha256: str
    truncated: bool
    binary: bool


@dataclass
class BoundedOutput:
    limit_bytes: int
    _buffer: bytearray = field(default_factory=bytearray)
    _hasher: object = field(default_factory=hashlib.sha256)
    bytes_seen: int = 0
    truncated: bool = False
    binary: bool = False

    def __post_init__(self) -> None:
        if self.limit_bytes <= 0:
            raise ValueError("limit_bytes must be positive")

    def append(self, data: bytes) -> None:
        self.bytes_seen += len(data)
        self._hasher.update(data)  # type: ignore[attr-defined]
        self.binary = self.binary or b"\x00" in data
        remaining = self.limit_bytes - len(self._buffer)
        if remaining > 0:
            self._buffer.extend(data[:remaining])
        if len(data) > max(remaining, 0):
            self.truncated = True

    def text(self, encoding: str) -> str:
        data = bytes(self._buffer)
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            self.binary = True
            return data.decode(encoding, errors="replace")

    def metadata(self) -> OutputMetadata:
        return OutputMetadata(
            bytes_seen=self.bytes_seen,
            sha256=self._hasher.hexdigest(),  # type: ignore[attr-defined]
            truncated=self.truncated,
            binary=self.binary,
        )
