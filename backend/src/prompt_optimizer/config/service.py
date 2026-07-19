from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Literal
from uuid import uuid4

from prompt_optimizer.paths import app_data_dir
from prompt_optimizer.public import register_runtime_secret
from prompt_optimizer.secrets import (
    SecretStore,
    SecretStoreError,
    create_secret_store,
    new_secret_reference,
)

# RC IDs: RC-065, RC-180, RC-181. Resolve typed configuration and references safely.

ConfigLayer = Literal["default", "user", "workspace", "env", "session", "cli"]
ValueKind = Literal["string", "integer", "number"]
_ALL_OVERRIDES: frozenset[ConfigLayer] = frozenset(
    {"user", "workspace", "env", "session", "cli"}
)
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class ConfigReference:
    kind: Literal["env", "keychain"]
    target: str


def parse_config_reference(value: object) -> ConfigReference | None:
    if not isinstance(value, str):
        return None
    if value.startswith("env:"):
        target = value.removeprefix("env:")
        if not _ENV_NAME.fullmatch(target):
            raise ValueError("env reference must contain a valid environment variable name.")
        return ConfigReference("env", target)
    if value.startswith("keychain:"):
        target = value.removeprefix("keychain:")
        if not target.startswith("secret://rabbit-code/"):
            raise ValueError("keychain reference must contain an opaque SecretStore reference.")
        return ConfigReference("keychain", target)
    if value.startswith("secret://rabbit-code/"):
        return ConfigReference("keychain", value)
    return None


@dataclass(frozen=True)
class ConfigField:
    value_kind: ValueKind
    default: object
    sensitive: bool
    scope: str
    allowed_layers: frozenset[ConfigLayer]
    nullable: bool = False
    minimum: int | float | None = None


CONFIG_FIELDS: dict[str, ConfigField] = {
    "provider": ConfigField("string", "offline", False, "runtime", _ALL_OVERRIDES),
    "model": ConfigField("string", None, False, "provider", _ALL_OVERRIDES, nullable=True),
    "base_url": ConfigField("string", None, False, "provider", _ALL_OVERRIDES, nullable=True),
    "api_key": ConfigField(
        "string",
        None,
        True,
        "user-secret",
        frozenset({"user", "workspace", "env", "session", "cli"}),
        nullable=True,
    ),
    "timeout_seconds": ConfigField(
        "number",
        20.0,
        False,
        "runtime",
        _ALL_OVERRIDES,
        minimum=0.1,
    ),
    "max_retries": ConfigField(
        "integer",
        2,
        False,
        "runtime",
        _ALL_OVERRIDES,
        minimum=0,
    ),
    "rate_limit_per_minute": ConfigField(
        "integer",
        30,
        False,
        "runtime",
        _ALL_OVERRIDES,
        minimum=1,
    ),
}


@dataclass(frozen=True)
class _ResolvedValue:
    value: object
    source: ConfigLayer
    field: ConfigField
    source_kind: str


class ConfigSnapshot:
    def __init__(self, entries: dict[str, _ResolvedValue]) -> None:
        self._entries = entries

    def values(self) -> dict[str, object]:
        return {name: entry.value for name, entry in self._entries.items()}

    def source_of(self, name: str) -> ConfigLayer:
        try:
            return self._entries[name].source
        except KeyError as exc:
            raise KeyError(f"未知配置项：{name}") from exc

    def display(self) -> dict[str, dict[str, object]]:
        displayed: dict[str, dict[str, object]] = {}
        for name, entry in self._entries.items():
            if entry.field.sensitive:
                value: object = (
                    f"secret://config/{name}" if entry.value is not None else "<not configured>"
                )
            else:
                value = entry.value if entry.value is not None else "<not configured>"
            displayed[name] = {
                "value": value,
                "source": entry.source,
                "source_kind": entry.source_kind,
                "source_label": _source_label(entry.source_kind),
                "sensitive": entry.field.sensitive,
                "scope": entry.field.scope,
            }
        return displayed


class ConfigService:
    """Load user/workspace files and merge transient session/CLI overrides."""

    def __init__(
        self,
        *,
        user_path: Path | None = None,
        workspace_root: Path | None = None,
        secret_store: SecretStore | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self.user_path = user_path or (app_data_dir() / "config.json")
        self.workspace_path = (
            workspace_root / ".rabbit-code" / "config.json" if workspace_root else None
        )
        self.secret_store = secret_store or create_secret_store()
        self.environment = environment if environment is not None else os.environ

    def resolve(
        self,
        *,
        session: dict[str, object] | None = None,
        cli: dict[str, object] | None = None,
    ) -> ConfigSnapshot:
        entries = {
            name: _ResolvedValue(field.default, "default", field, "default")
            for name, field in CONFIG_FIELDS.items()
        }
        layers: list[tuple[ConfigLayer, dict[str, object]]] = [
            ("user", self._load_file(self.user_path)),
            ("workspace", self._load_file(self.workspace_path)),
            ("env", self._load_environment()),
            ("session", session or {}),
            ("cli", cli or {}),
        ]
        for layer, values in layers:
            self._validate_layer(layer, values)
            for name, value in values.items():
                resolved = self._resolve_value(layer, name, value)
                entries[name] = _ResolvedValue(
                    resolved,
                    layer,
                    CONFIG_FIELDS[name],
                    _source_kind(layer, name, value),
                )
        return ConfigSnapshot(entries)

    def set_user_secret(self, name: str, value: str) -> str:
        field = CONFIG_FIELDS.get(name)
        if field is None or not field.sensitive:
            raise ValueError(f"配置项 {name} 不是敏感字段。")
        if not value:
            raise ValueError("凭据不能为空。")
        reference = new_secret_reference()
        self.secret_store.put(reference, value)
        payload = self._load_file(self.user_path)
        previous = payload.get(name)
        payload[name] = reference
        try:
            self._write_file(self.user_path, payload)
        except Exception:
            self.secret_store.delete(reference)
            raise
        if isinstance(previous, str) and previous.startswith("secret://rabbit-code/"):
            self.secret_store.delete(previous)
        return reference

    def delete_user_secret(self, name: str) -> bool:
        field = CONFIG_FIELDS.get(name)
        if field is None or not field.sensitive:
            raise ValueError(f"配置项 {name} 不是敏感字段。")
        payload = self._load_file(self.user_path)
        previous = payload.pop(name, None)
        if previous is None:
            return False
        self._write_file(self.user_path, payload)
        if isinstance(previous, str) and previous.startswith("secret://rabbit-code/"):
            self.secret_store.delete(previous)
        return True

    def _resolve_value(self, layer: ConfigLayer, name: str, value: object) -> object:
        if value is None:
            return value
        reference = parse_config_reference(value)
        if reference is not None:
            if reference.kind == "env":
                resolved = self.environment.get(reference.target)
                if resolved is None:
                    raise ValueError(f"环境变量未设置：{reference.target}")
                if CONFIG_FIELDS[name].sensitive:
                    register_runtime_secret(resolved)
                return _coerce_environment_value(name, resolved)
            try:
                secret = self.secret_store.get(reference.target)
            except SecretStoreError as exc:
                raise ValueError("无法读取 Provider 凭据；安全凭据存储不可用。") from exc
            if secret is None:
                raise ValueError("Provider 凭据 reference 不存在。")
            register_runtime_secret(secret)
            return secret
        if layer in {"user", "workspace"} and CONFIG_FIELDS[name].sensitive:
            raise ValueError("配置中的敏感字段必须使用 opaque env: 或 keychain: reference。")
        if layer == "env" and CONFIG_FIELDS[name].sensitive and isinstance(value, str):
            register_runtime_secret(value)
        return _coerce_environment_value(name, value) if layer == "env" else value

    def _load_environment(self) -> dict[str, object]:
        values: dict[str, object] = {}
        for name in CONFIG_FIELDS:
            suffix = name.upper()
            preferred = f"RABBIT_CODE_{suffix}"
            legacy = f"PROMPT_OPTIMIZER_{suffix}"
            if preferred in self.environment:
                values[name] = self.environment[preferred]
            elif legacy in self.environment:
                values[name] = self.environment[legacy]
        return values

    @staticmethod
    def _load_file(path: Path | None) -> dict[str, object]:
        if path is None or not path.is_file():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, JSONDecodeError) as exc:
            raise ValueError(f"无法读取配置文件：{path}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"配置文件必须是 JSON 对象：{path}")
        return {str(name): value for name, value in payload.items()}

    @staticmethod
    def _write_file(path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def _validate_layer(self, layer: ConfigLayer, values: dict[str, object]) -> None:
        for name, value in values.items():
            field = CONFIG_FIELDS.get(name)
            if field is None:
                raise ValueError(f"未知配置项：{name}")
            if layer not in field.allowed_layers:
                raise ValueError(f"配置项 {name} 不允许在 {layer} 层覆盖。")
            if value is None:
                if field.nullable:
                    continue
                raise ValueError(f"配置项 {name} 不能为 null。")
            reference = parse_config_reference(value)
            if reference is not None and reference.kind == "env":
                environment_value = self.environment.get(reference.target)
                if environment_value is None:
                    raise ValueError(f"环境变量未设置：{reference.target}")
                value = _coerce_environment_value(name, environment_value)
            elif layer == "env":
                value = _coerce_environment_value(name, value)
            if field.value_kind == "string" and not isinstance(value, str):
                raise ValueError(f"配置项 {name} 必须是字符串。")
            if field.value_kind == "integer" and (
                not isinstance(value, int) or isinstance(value, bool)
            ):
                raise ValueError(f"配置项 {name} 必须是整数。")
            if field.value_kind == "number" and (
                not isinstance(value, (int, float)) or isinstance(value, bool)
            ):
                raise ValueError(f"配置项 {name} 必须是数字。")
            if field.minimum is not None and value < field.minimum:  # type: ignore[operator]
                raise ValueError(f"配置项 {name} 必须大于等于 {field.minimum}。")


def _source_kind(layer: ConfigLayer, name: str, value: object) -> str:
    reference = parse_config_reference(value)
    if reference is not None:
        return "environment" if reference.kind == "env" else "keychain"
    if layer == "env":
        return "environment"
    if layer == "user" and CONFIG_FIELDS[name].sensitive:
        return "keychain"
    return layer


def _coerce_environment_value(name: str, value: object) -> object:
    field = CONFIG_FIELDS[name]
    if field.value_kind == "integer":
        try:
            return int(str(value))
        except ValueError as exc:
            raise ValueError(f"环境变量中的配置项 {name} 必须是整数。") from exc
    if field.value_kind == "number":
        try:
            return float(str(value))
        except ValueError as exc:
            raise ValueError(f"环境变量中的配置项 {name} 必须是数字。") from exc
    return value


def _source_label(source_kind: str) -> str:
    return {
        "default": "default",
        "user": "user config",
        "workspace": "workspace config",
        "environment": "environment variable",
        "keychain": "keychain",
        "session": "session",
        "cli": "CLI",
    }.get(source_kind, source_kind)
