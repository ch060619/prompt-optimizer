from __future__ import annotations

import argparse
from pathlib import Path

from prompt_optimizer.storage.backup import backup_database, read_schema_version

# RC ID: RC-053. Create an explicit database/config backup before maintenance.


def main() -> None:
    parser = argparse.ArgumentParser(description="Back up a Rabbit Code SQLite database.")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    output_dir = args.output_dir or args.database.parent / "backups"
    result = backup_database(
        args.database,
        output_dir,
        schema_version=read_schema_version(args.database),
        target_schema_version=1,
        config_path=args.config,
    )
    print(result.manifest_path)


if __name__ == "__main__":
    main()
