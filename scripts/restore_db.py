from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--backup", required=True, type=Path)
parser.add_argument("--database", required=True, type=Path)
args = parser.parse_args()
args.database.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(args.backup) as source, sqlite3.connect(args.database) as target:
    source.backup(target)
print(f"Database restored to {args.database}")
