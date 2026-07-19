from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from typing import Any

# RC ID: RC-208. Establish one provenance, permission, and lifecycle registry for extensions.


class TrustError(PermissionError):
    pass


class TrustApprovalRequired(TrustError, PermissionError):
    pass


class TrustReapprovalRequired(TrustError, PermissionError):
    pass


@dataclass(frozen=True)
class TrustManifest:
    kind: str
    name: str
    version: str
    source: str
    sha256: str
    permissions: frozenset[str]

    def __post_init__(self) -> None:
        if self.kind not in {"plugin", "skill", "hook", "mcp", "script"}:
            raise ValueError("unsupported trust manifest kind")
        if not re.fullmatch(r"[a-z][a-z0-9_.-]{1,63}", self.name):
            raise ValueError("trust manifest name is invalid")
        if not re.fullmatch(r"\d+\.\d+\.\d+", self.version):
            raise ValueError("trust manifest version is invalid")
        if not self.source.strip():
            raise ValueError("trust manifest source is required")
        if not re.fullmatch(r"[0-9a-f]{64}", self.sha256.lower()):
            raise ValueError("trust manifest sha256 is invalid")

    @property
    def record_id(self) -> str:
        return f"{self.kind}:{self.name}"

    def as_mapping(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "name": self.name,
            "version": self.version,
            "source": self.source,
            "sha256": self.sha256.lower(),
            "permissions": sorted(self.permissions),
        }


@dataclass(frozen=True)
class TrustRecord:
    manifest: TrustManifest
    enabled: bool = False
    locked: bool = False


@dataclass(frozen=True)
class TrustExecutionContext:
    manifest: TrustManifest
    permissions: frozenset[str]
    isolated: bool = True


TrustHandler = Callable[[TrustExecutionContext, Mapping[str, Any]], Any]


class TrustRegistry:
    def __init__(
        self,
        *,
        allowed_sources: set[str] | frozenset[str],
        allowed_permissions: set[str] | frozenset[str],
    ) -> None:
        self.allowed_sources = frozenset(allowed_sources)
        self.allowed_permissions = frozenset(allowed_permissions)
        self._records: dict[str, TrustRecord] = {}

    def list_records(self) -> tuple[TrustRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def get(self, record_id: str) -> TrustRecord:
        try:
            return self._records[record_id]
        except KeyError as exc:
            raise TrustError(f"trusted source is not registered: {record_id}") from exc

    def register(
        self,
        manifest: TrustManifest,
        *,
        artifact: bytes | None = None,
        explicit_confirmation: bool = False,
    ) -> TrustRecord:
        self._validate_manifest(manifest, artifact)
        current = self._records.get(manifest.record_id)
        if current is None and not explicit_confirmation:
            raise TrustApprovalRequired("source trust requires explicit confirmation")
        if current is not None:
            changed = current.manifest != manifest
            if changed and current.locked:
                raise TrustReapprovalRequired("source changed while trust record is locked")
            if changed and not explicit_confirmation:
                raise TrustReapprovalRequired("source or permissions changed; reapproval required")
            if not changed and not explicit_confirmation:
                raise TrustApprovalRequired("source trust requires explicit confirmation")
        record = TrustRecord(manifest, enabled=True, locked=current.locked if current else False)
        self._records[manifest.record_id] = record
        return record

    def lock(self, record_id: str) -> TrustRecord:
        record = self.get(record_id)
        updated = replace(record, locked=True)
        self._records[record_id] = updated
        return updated

    def unlock(self, record_id: str, *, explicit_confirmation: bool = False) -> TrustRecord:
        if not explicit_confirmation:
            raise TrustApprovalRequired("unlock requires explicit confirmation")
        record = self.get(record_id)
        updated = replace(record, locked=False)
        self._records[record_id] = updated
        return updated

    def disable(self, record_id: str) -> TrustRecord:
        record = self.get(record_id)
        updated = replace(record, enabled=False)
        self._records[record_id] = updated
        return updated

    def enable(self, record_id: str, *, explicit_confirmation: bool = False) -> TrustRecord:
        if not explicit_confirmation:
            raise TrustApprovalRequired("enable requires explicit confirmation")
        record = self.get(record_id)
        updated = replace(record, enabled=True)
        self._records[record_id] = updated
        return updated

    def revoke(self, record_id: str) -> TrustRecord:
        return self.disable(record_id)

    def execute(
        self,
        record_id: str,
        payload: Mapping[str, Any],
        handler: TrustHandler,
    ) -> Any:
        record = self.get(record_id)
        if not record.enabled:
            raise TrustError(f"trusted source is disabled: {record_id}")
        context = TrustExecutionContext(record.manifest, record.manifest.permissions)
        return handler(context, payload)

    def _validate_manifest(self, manifest: TrustManifest, artifact: bytes | None) -> None:
        if manifest.source not in self.allowed_sources:
            raise TrustError(f"trust source is not allowlisted: {manifest.source}")
        if not manifest.permissions <= self.allowed_permissions:
            raise TrustError("trust manifest declares an unapproved permission")
        if artifact is not None:
            digest = hashlib.sha256(artifact).hexdigest()
            if digest != manifest.sha256.lower():
                raise TrustError("trust artifact hash does not match manifest")
