from __future__ import annotations

import hashlib
import json
import zipfile
from collections.abc import Collection, Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

# RC ID: RC-221. Keep portable data versioned, bounded, and credential-free.

PORTABLE_SCHEMA_VERSION: Final[Literal["rc221-v1"]] = "rc221-v1"
PORTABLE_JSON_MAX_BYTES = 8_000_000
PORTABLE_ARCHIVE_MAX_BYTES = 10_000_000
PORTABLE_ENTRY_MAX_BYTES = 5_000_000
PORTABLE_MAX_ENTRIES = 128

_PORTABLE_SETTING_KEYS = frozenset(
    {
        "theme",
        "language",
        "shell",
        "permissionMode",
        "sandbox",
        "network",
        "retainLogs",
        "savePromptHistory",
        "telemetry",
        "telemetryConsentVersion",
        "autoUpdate",
        "notifications",
        "tray",
        "shortcutPreset",
        "mcp",
        "plugins",
        "logLevel",
    }
)
_SENSITIVE_KEY_PARTS = frozenset(
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


class PortableFormatError(ValueError):
    """Raised when portable data fails schema or archive safety validation."""


class PortableMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    role: str = Field(min_length=1, max_length=32)
    content: str = Field(max_length=1_000_000)
    created_at: str | None = None


class PortableSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=500)
    messages: list[PortableMessage] = Field(default_factory=list, max_length=10_000)
    pinned: bool = False
    archived: bool = False
    deleted: bool = False
    parent_id: str | None = None


class PortablePrompt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    original_prompt: str = Field(max_length=1_000_000)
    optimized_prompt: str = Field(max_length=1_000_000)
    analysis: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    accepted: bool = False
    provider_used: str | None = None
    model: str | None = None


class PortableTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=500)
    category: str = Field(min_length=1, max_length=128)
    description: str = Field(max_length=10_000)
    tags: list[str] = Field(default_factory=list, max_length=100)
    template: str = Field(max_length=1_000_000)
    variables: list[str] = Field(default_factory=list, max_length=100)
    best_practices: list[str] = Field(default_factory=list, max_length=100)


class PortableDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["rc221-v1"]
    workspace: dict[str, str] = Field(default_factory=dict)
    sessions: list[PortableSession] = Field(default_factory=list, max_length=10_000)
    prompts: list[PortablePrompt] = Field(default_factory=list, max_length=10_000)
    templates: list[PortableTemplate] = Field(default_factory=list, max_length=10_000)
    settings: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class PortableImportPreview:
    schema_version: str
    counts: Mapping[str, int]
    conflicts: Mapping[str, tuple[str, ...]]
    conflict_strategies: tuple[str, ...] = ("skip", "replace")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "counts": dict(self.counts),
            "conflicts": {key: list(value) for key, value in self.conflicts.items()},
            "conflict_strategies": list(self.conflict_strategies),
        }


class PortableBundleService:
    """Build and validate a portable JSON/ZIP payload without touching storage."""

    def export_json(
        self,
        *,
        sessions: Iterable[object] = (),
        prompts: Iterable[object] = (),
        templates: Iterable[object] = (),
        settings: Mapping[str, object] | None = None,
        workspace: Mapping[str, object] | None = None,
    ) -> bytes:
        document = self.build_document(
            sessions=sessions,
            prompts=prompts,
            templates=templates,
            settings=settings,
            workspace=workspace,
        )
        payload = _json_bytes(document.model_dump(mode="json"))
        _ensure_size(payload, PORTABLE_JSON_MAX_BYTES, "portable JSON")
        return payload

    def export_zip(
        self,
        *,
        sessions: Iterable[object] = (),
        prompts: Iterable[object] = (),
        templates: Iterable[object] = (),
        settings: Mapping[str, object] | None = None,
        workspace: Mapping[str, object] | None = None,
    ) -> bytes:
        data = self.export_json(
            sessions=sessions,
            prompts=prompts,
            templates=templates,
            settings=settings,
            workspace=workspace,
        )
        manifest = {
            "schema_version": PORTABLE_SCHEMA_VERSION,
            "format": "zip",
            "files": [
                {
                    "path": "data.json",
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            ],
        }
        output = BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            _write_zip_entry(archive, "manifest.json", _json_bytes(manifest))
            _write_zip_entry(archive, "data.json", data)
        result = output.getvalue()
        _ensure_size(result, PORTABLE_ARCHIVE_MAX_BYTES, "portable ZIP")
        return result

    def build_document(
        self,
        *,
        sessions: Iterable[object] = (),
        prompts: Iterable[object] = (),
        templates: Iterable[object] = (),
        settings: Mapping[str, object] | None = None,
        workspace: Mapping[str, object] | None = None,
    ) -> PortableDocument:
        document = PortableDocument(
            schema_version=PORTABLE_SCHEMA_VERSION,
            workspace=_portable_workspace(workspace or {}),
            sessions=[_session(value, index) for index, value in enumerate(sessions)],
            prompts=[_prompt(value) for value in prompts],
            templates=[_template(value) for value in templates],
            settings=_portable_settings(settings or {}),
        )
        _assert_unique_ids(document)
        return document

    def preview(
        self,
        source: bytes,
        *,
        existing_ids: Mapping[str, Collection[str]] | None = None,
    ) -> PortableImportPreview:
        document = self.parse(source)
        return self._preview_document(document, existing_ids or {})

    def import_document(
        self,
        source: bytes,
        *,
        existing_ids: Mapping[str, Collection[str]] | None = None,
        conflict_strategy: Literal["skip", "replace"] = "skip",
    ) -> PortableDocument:
        if conflict_strategy not in {"skip", "replace"}:
            raise ValueError("conflict_strategy must be 'skip' or 'replace'")
        document = self.parse(source)
        if conflict_strategy == "replace":
            return document
        conflicts = self._preview_document(document, existing_ids or {}).conflicts
        message_conflicts = set(conflicts.get("messages", ()))
        session_conflicts = set(conflicts.get("sessions", ()))
        return document.model_copy(
            update={
                "sessions": [
                    item.model_copy(
                        update={
                            "messages": [
                                message
                                for message in item.messages
                                if message.id not in message_conflicts
                            ]
                        }
                    )
                    for item in document.sessions
                    if item.id not in session_conflicts
                ],
                "prompts": [
                    item for item in document.prompts if item.id not in conflicts.get("prompts", ())
                ],
                "templates": [
                    item
                    for item in document.templates
                    if item.id not in conflicts.get("templates", ())
                ],
                "settings": {
                    key: value
                    for key, value in document.settings.items()
                    if key not in conflicts.get("settings", ())
                },
            }
        )

    def parse(self, source: bytes) -> PortableDocument:
        if not isinstance(source, bytes) or not source:
            raise PortableFormatError("portable source must be non-empty bytes")
        if len(source) > PORTABLE_ARCHIVE_MAX_BYTES:
            raise PortableFormatError("portable source exceeds the size limit")
        if source.startswith(b"PK\x03\x04"):
            payload = _read_zip(source)
        else:
            payload = source
            _ensure_size(payload, PORTABLE_JSON_MAX_BYTES, "portable JSON")
        try:
            raw = json.loads(payload.decode("utf-8"))
            document = PortableDocument.model_validate(raw)
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as exc:
            raise PortableFormatError("portable document schema validation failed") from exc
        _assert_no_sensitive_keys(document.model_dump(mode="python"))
        _assert_unique_ids(document)
        return document

    @staticmethod
    def _preview_document(
        document: PortableDocument,
        existing_ids: Mapping[str, Collection[str]],
    ) -> PortableImportPreview:
        entity_ids = _entity_ids(document)
        conflicts = {
            kind: tuple(item_id for item_id in ids if item_id in set(existing_ids.get(kind, ())))
            for kind, ids in entity_ids.items()
        }
        return PortableImportPreview(
            schema_version=document.schema_version,
            counts={kind: len(ids) for kind, ids in entity_ids.items()},
            conflicts={kind: ids for kind, ids in conflicts.items() if ids},
        )


def _session(value: object, index: int) -> PortableSession:
    payload = _mapping(value)
    session_id = _identifier(payload.get("id"), f"session-{index}")
    raw_messages = payload.get("messages", ())
    if not isinstance(raw_messages, Iterable) or isinstance(raw_messages, (str, bytes)):
        raise PortableFormatError("session messages must be a sequence")
    messages = [
        _message(message, session_id, message_index)
        for message_index, message in enumerate(raw_messages)
    ]
    return PortableSession(
        id=session_id,
        title=_text(payload.get("title"), session_id),
        messages=messages,
        pinned=bool(payload.get("pinned", False)),
        archived=bool(payload.get("archived", False)),
        deleted=bool(payload.get("deleted", False)),
        parent_id=_optional_text(payload.get("parent_id")),
    )


def _message(value: object, session_id: str, index: int) -> PortableMessage:
    if isinstance(value, str):
        return PortableMessage(id=f"{session_id}:message:{index}", role="user", content=value)
    payload = _mapping(value)
    content = payload.get("content", payload.get("text", ""))
    if not isinstance(content, str):
        raise PortableFormatError("message content must be text")
    return PortableMessage(
        id=_identifier(payload.get("id"), f"{session_id}:message:{index}"),
        role=_text(payload.get("role"), "user"),
        content=content,
        created_at=_optional_text(payload.get("created_at")),
    )


def _prompt(value: object) -> PortablePrompt:
    payload = _mapping(value)
    analysis = payload.get("analysis", {})
    if not isinstance(analysis, Mapping):
        raise PortableFormatError("prompt analysis must be an object")
    return PortablePrompt(
        id=_identifier(payload.get("id"), "prompt"),
        original_prompt=_text(payload.get("original_prompt"), ""),
        optimized_prompt=_text(payload.get("optimized_prompt"), ""),
        analysis=dict(analysis),
        created_at=_optional_text(payload.get("created_at")),
        accepted=bool(payload.get("accepted", False)),
        provider_used=_optional_text(payload.get("provider_used")),
        model=_optional_text(payload.get("model")),
    )


def _template(value: object) -> PortableTemplate:
    payload = _mapping(value)
    return PortableTemplate(
        id=_identifier(payload.get("id"), "template"),
        name=_text(payload.get("name"), "template"),
        category=_text(payload.get("category"), "general"),
        description=_text(payload.get("description"), ""),
        tags=_text_list(payload.get("tags", [])),
        template=_text(payload.get("template"), ""),
        variables=_text_list(payload.get("variables", [])),
        best_practices=_text_list(payload.get("best_practices", [])),
    )


def _portable_workspace(settings: Mapping[str, object]) -> dict[str, str]:
    return {
        key: value
        for key in ("id", "name")
        if isinstance(value := settings.get(key), str) and value.strip()
    }


def _portable_settings(settings: Mapping[str, object]) -> dict[str, Any]:
    return {
        key: value
        for key, value in settings.items()
        if key in _PORTABLE_SETTING_KEYS and not _contains_sensitive_key(key)
    }


def _mapping(value: object) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    raise PortableFormatError("portable entity must be a model, dataclass, or object")


def _text(value: object, default: str) -> str:
    return value if isinstance(value, str) else default


def _identifier(value: object, default: str) -> str:
    if isinstance(value, (str, int)) and str(value).strip():
        return str(value)
    return default


def _optional_text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _text_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
        raise PortableFormatError("portable text lists must be sequences")
    return [item for item in value if isinstance(item, str)]


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _write_zip_entry(archive: zipfile.ZipFile, name: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, payload)


def _read_zip(source: bytes) -> bytes:
    try:
        with zipfile.ZipFile(BytesIO(source)) as archive:
            infos = archive.infolist()
            if len(infos) > PORTABLE_MAX_ENTRIES:
                raise PortableFormatError("portable ZIP has too many entries")
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                raise PortableFormatError("portable ZIP contains duplicate entries")
            for info in infos:
                _validate_zip_name(info.filename)
            if set(names) != {"manifest.json", "data.json"}:
                raise PortableFormatError("portable ZIP must contain manifest.json and data.json")
            for info in infos:
                if info.is_dir() or info.file_size > PORTABLE_ENTRY_MAX_BYTES:
                    raise PortableFormatError("portable ZIP contains an invalid entry size")
                mode = (info.external_attr >> 16) & 0o170000
                if mode == 0o120000:
                    raise PortableFormatError("portable ZIP symlinks are not allowed")
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            if (
                not isinstance(manifest, Mapping)
                or manifest.get("schema_version") != PORTABLE_SCHEMA_VERSION
            ):
                raise PortableFormatError("portable ZIP manifest version is unsupported")
            data = archive.read("data.json")
            files = manifest.get("files")
            if not isinstance(files, list) or files != [
                {
                    "path": "data.json",
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            ]:
                raise PortableFormatError("portable ZIP manifest does not match data.json")
            return data
    except PortableFormatError:
        raise
    except (
        OSError,
        RuntimeError,
        ValueError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        zipfile.BadZipFile,
    ) as exc:
        raise PortableFormatError("portable ZIP validation failed") from exc


def _validate_zip_name(name: str) -> None:
    if (
        not name
        or "\\" in name
        or "\x00" in name
        or name.startswith("/")
        or PurePosixPath(name).is_absolute()
        or ".." in PurePosixPath(name).parts
        or len(PurePosixPath(name).parts) != 1
    ):
        raise PortableFormatError("portable ZIP path traversal is not allowed")


def _ensure_size(payload: bytes, maximum: int, label: str) -> None:
    if len(payload) > maximum:
        raise PortableFormatError(f"{label} exceeds the size limit")


def _contains_sensitive_key(key: object) -> bool:
    normalized = str(key).replace("_", "").replace("-", "").casefold()
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _assert_no_sensitive_keys(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _contains_sensitive_key(key):
                raise PortableFormatError("portable data cannot contain credential fields")
            _assert_no_sensitive_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_sensitive_keys(item)


def _entity_ids(document: PortableDocument) -> dict[str, tuple[str, ...]]:
    return {
        "sessions": tuple(item.id for item in document.sessions),
        "messages": tuple(
            message.id for session in document.sessions for message in session.messages
        ),
        "prompts": tuple(item.id for item in document.prompts),
        "templates": tuple(item.id for item in document.templates),
        "settings": tuple(document.settings),
    }


def _assert_unique_ids(document: PortableDocument) -> None:
    for kind, ids in _entity_ids(document).items():
        if len(ids) != len(set(ids)):
            raise PortableFormatError(f"portable document contains duplicate {kind} IDs")
