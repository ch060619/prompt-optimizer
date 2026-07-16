from __future__ import annotations

import os
import warnings
from pathlib import Path

from prompt_optimizer.identity import (
    DISTRIBUTION_NAME,
    LEGACY_COMPATIBILITY_CUTOFF,
    LEGACY_DISTRIBUTION_NAME,
    compatible_env,
)

# RC ID: RC-054. Prefer Rabbit Code paths and discover legacy Prompt Optimizer data.

PACKAGE_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = PACKAGE_ROOT.parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parents[2]
DATA_ROOT = PROJECT_ROOT / "data"


def app_data_dir() -> Path:
    new_custom = os.getenv("RABBIT_CODE_HOME")
    legacy_custom = os.getenv("PROMPT_OPTIMIZER_HOME")
    custom = new_custom or legacy_custom
    if custom:
        if new_custom is None and legacy_custom is not None:
            warnings.warn(
                "PROMPT_OPTIMIZER_HOME 已弃用，请迁移到 RABBIT_CODE_HOME；"
                f"兼容截止 Rabbit Code {LEGACY_COMPATIBILITY_CUTOFF}。",
                DeprecationWarning,
                stacklevel=2,
            )
        path = Path(custom).expanduser()
    elif os.name == "nt":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        path = _default_data_dir(base)
    else:
        data_home = os.getenv("XDG_DATA_HOME")
        base = Path(data_home) if data_home else Path.home() / ".local" / "share"
        path = _default_data_dir(base)
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_db_path() -> Path:
    custom = compatible_env("DB")
    if custom:
        return Path(custom).expanduser()
    data_dir = app_data_dir()
    database_name = (
        "prompt_optimizer.sqlite3"
        if data_dir.name == LEGACY_DISTRIBUTION_NAME
        else "rabbit-code.sqlite3"
    )
    return data_dir / database_name


def _default_data_dir(base: Path) -> Path:
    current = base / DISTRIBUTION_NAME
    legacy = base / LEGACY_DISTRIBUTION_NAME
    if not current.exists() and legacy.exists():
        warnings.warn(
            f"检测到旧数据目录 {legacy}，已自动兼容读取；请迁移到 {current}，"
            f"兼容截止 Rabbit Code {LEGACY_COMPATIBILITY_CUTOFF}。",
            DeprecationWarning,
            stacklevel=2,
        )
        return legacy
    return current
