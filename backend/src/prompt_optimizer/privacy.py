from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from prompt_optimizer.public import sanitize_secret_text

# RC IDs: RC-210, RC-220. Keep telemetry opt-in, versioned, local, and redacted.


TELEMETRY_CONSENT_VERSION = "rc220-v1"


class PrivacyConsentRequired(PermissionError):
    """Raised when a user action is required before sending private data."""


@dataclass(frozen=True)
class TelemetryConsent:
    enabled: bool = False
    include_content: bool = False
    consent_version: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "include_content": self.include_content,
            "consent_version": self.consent_version,
        }


TelemetrySender = Callable[[tuple[Mapping[str, Any], ...]], None]


class TelemetryService:
    def __init__(self) -> None:
        self._consent = TelemetryConsent()
        self._events: list[dict[str, Any]] = []

    @property
    def consent(self) -> TelemetryConsent:
        return self._consent

    def opt_in(
        self,
        *,
        include_content: bool = False,
        consent_version: str = TELEMETRY_CONSENT_VERSION,
    ) -> TelemetryConsent:
        if not consent_version.strip():
            raise ValueError("consent_version must not be empty")
        self._consent = TelemetryConsent(
            enabled=True,
            include_content=include_content,
            consent_version=consent_version,
        )
        return self._consent

    def revoke(self) -> TelemetryConsent:
        self._consent = TelemetryConsent()
        return self._consent

    def clear(self) -> None:
        self._events.clear()

    def record(
        self,
        event_name: str,
        metadata: Mapping[str, Any],
        *,
        content: str | None = None,
    ) -> bool:
        if not self._consent.enabled:
            return False
        removed: set[str] = set()
        safe_metadata = _without_content(_sanitize_public_payload(metadata), removed)
        event: dict[str, Any] = {
            "event": event_name,
            "consent_version": self._consent.consent_version,
            "metadata": safe_metadata,
        }
        if content is not None and self._consent.include_content:
            event["content"] = _sanitize_public_payload(content)
        self._events.append(event)
        return True

    def pending_events(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(dict(event) for event in self._events)

    def send(self, *, confirm: bool, sender: TelemetrySender) -> bool:
        if not self._consent.enabled or not self._events:
            return False
        if not confirm:
            raise PrivacyConsentRequired("explicit telemetry send confirmation is required")
        sender(tuple(dict(event) for event in self._events))
        self.clear()
        return True


@dataclass(frozen=True)
class DiagnosticFile:
    name: str
    size_bytes: int

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "size_bytes": self.size_bytes}


@dataclass(frozen=True)
class DiagnosticPreview:
    metadata: Mapping[str, Any]
    files: tuple[DiagnosticFile, ...]
    redacted_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "metadata": dict(self.metadata),
            "files": [item.to_dict() for item in self.files],
            "redacted_fields": list(self.redacted_fields),
        }


DiagnosticSender = Callable[[Mapping[str, object]], None]


class DiagnosticBundleService:
    def __init__(self) -> None:
        self._pending: DiagnosticPreview | None = None

    @property
    def pending(self) -> DiagnosticPreview | None:
        return self._pending

    def preview(
        self,
        metadata: Mapping[str, Any],
        files: Mapping[str, bytes | str],
    ) -> DiagnosticPreview:
        removed: set[str] = set()
        safe_metadata = _without_content(_sanitize_public_payload(metadata), removed)
        safe_files = tuple(
            DiagnosticFile(Path(str(name)).name or "diagnostic", _size_bytes(value))
            for name, value in sorted(files.items())
        )
        self._pending = DiagnosticPreview(
            metadata=safe_metadata,
            files=safe_files,
            redacted_fields=tuple(sorted(removed)),
        )
        return self._pending

    def export(self, *, confirm: bool) -> str:
        preview = self._require_confirmed(confirm)
        return json.dumps(preview.to_dict(), ensure_ascii=False, sort_keys=True)

    def send(self, *, confirm: bool, sender: DiagnosticSender) -> None:
        preview = self._require_confirmed(confirm)
        sender(preview.to_dict())
        self._pending = None

    def clear(self) -> None:
        self._pending = None

    def _require_confirmed(self, confirm: bool) -> DiagnosticPreview:
        if not confirm:
            raise PrivacyConsentRequired("explicit diagnostic send confirmation is required")
        if self._pending is None:
            raise ValueError("diagnostic preview is required before sending")
        return self._pending


_CONTENT_KEYS = frozenset(
    {
        "body",
        "code",
        "command",
        "content",
        "contents",
        "diff",
        "input",
        "messages",
        "output",
        "path",
        "prompt",
        "prompttext",
        "raw",
        "source",
        "stderr",
        "stdout",
    }
)

_SENSITIVE_KEYS = frozenset(
    {
        "apikey",
        "accesstoken",
        "authorization",
        "bearer",
        "cookie",
        "credential",
        "password",
        "secret",
    }
)


def _sanitize_public_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): (
                "[REDACTED]"
                if str(key).replace("_", "").replace("-", "").casefold() in _SENSITIVE_KEYS
                else _sanitize_public_payload(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize_public_payload(item) for item in value]
    if isinstance(value, str):
        return sanitize_secret_text(value)
    return value


def _without_content(value: Any, removed: set[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"value": value}
    result: dict[str, Any] = {}
    for key, item in value.items():
        normalized = str(key).replace("_", "").replace("-", "").casefold()
        if normalized in _CONTENT_KEYS:
            removed.add(str(key))
            continue
        if isinstance(item, Mapping):
            result[str(key)] = _without_content(item, removed)
        elif isinstance(item, list):
            result[str(key)] = [
                _without_content(entry, removed) if isinstance(entry, Mapping) else entry
                for entry in item
            ]
        else:
            result[str(key)] = item
    return result


def _size_bytes(value: bytes | str) -> int:
    return len(value) if isinstance(value, bytes) else len(value.encode("utf-8"))
