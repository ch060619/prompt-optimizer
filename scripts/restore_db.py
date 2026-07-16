from __future__ import annotations

import argparse
from pathlib import Path

from prompt_optimizer.storage.backup import restore_database, verify_database

# RC ID: RC-053. Verify backups read-only and restore only with an explicit destination.


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify or restore a Rabbit Code SQLite backup.")
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--config-backup", type=Path)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    if args.check_only:
        print(verify_database(args.backup))
        return
    restore_database(
        args.backup,
        args.database,
        overwrite=args.overwrite,
        config_backup=args.config_backup,
        config_destination=args.config,
    )
    print(args.database)


if __name__ == "__main__":
    main()
