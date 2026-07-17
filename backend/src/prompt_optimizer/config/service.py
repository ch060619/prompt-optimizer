from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from prompt_optimizer.paths import app_data_dir

# RC ID: RC-065. Resolve typed configuration from default to CLI layers safely.

ConfigLayer = Literal["default", "user", "workspace", "session", "cli"]
ValueKind = Literal["string", "integer", "number"]
_ALL_OVERRIDES: frozenset[ConfigLayer] = frozenset(
    {"user", "workspace", "session", "cli"}
)


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
        frozenset({"user"}),
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
    ) -> None:
        self.user_path = user_path or (app_data_dir() / "config.json")
        self.workspace_path = (
            workspace_root / ".rabbit-code" / "config.json" if workspace_root else None
        )

    def resolve(
        self,
        *,
        session: dict[str, object] | None = None,
        cli: dict[str, object] | None = None,
    ) -> ConfigSnapshot:
        entries = {
            name: _ResolvedValue(field.default, "default", field)
            for name, field in CONFIG_FIELDS.items()
        }
        layers: list[tuple[ConfigLayer, dict[str, object]]] = [
            ("user", self._load_file(self.user_path)),
            ("workspace", self._load_file(self.workspace_path)),
            ("session", session or {}),
            ("cli", cli or {}),
        ]
        for layer, values in layers:
            self._validate_layer(layer, values)
            for name, value in values.items():
                entries[name] = _ResolvedValue(value, layer, CONFIG_FIELDS[name])
        return ConfigSnapshot(entries)

    @staticmethod
    def _load_file(path: Path | None) -> dict[str, object]:
        if path is None or not path.is_file():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"无法读取配置文件：{path}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"配置文件必须是 JSON 对象：{path}")
        return {str(name): value for name, value in payload.items()}

    @staticmethod
    def _validate_layer(layer: ConfigLayer, values: dict[str, object]) -> None:
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
