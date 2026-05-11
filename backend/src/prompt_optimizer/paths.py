from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = PACKAGE_ROOT.parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parents[2]
DATA_ROOT = PROJECT_ROOT / "data"


def app_data_dir() -> Path:
    custom = os.getenv("PROMPT_OPTIMIZER_HOME")
    if custom:
        path = Path(custom).expanduser()
    elif os.name == "nt":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        path = base / "prompt-optimizer"
    else:
        data_home = os.getenv("XDG_DATA_HOME")
        base = Path(data_home) if data_home else Path.home() / ".local" / "share"
        path = base / "prompt-optimizer"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_db_path() -> Path:
    custom = os.getenv("PROMPT_OPTIMIZER_DB")
    if custom:
        return Path(custom).expanduser()
    return app_data_dir() / "prompt_optimizer.sqlite3"
