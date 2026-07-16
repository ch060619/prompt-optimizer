from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--database", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(args.database) as source, sqlite3.connect(args.output) as target:
    source.backup(target)
print(f"Backup written to {args.output}")
