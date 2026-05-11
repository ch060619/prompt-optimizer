from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from prompt_optimizer.core.models import PromptAnalysis, PromptVersion, VersionSummary
from prompt_optimizer.paths import default_db_path


class StorageService:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def save_version(
        self,
        original_prompt: str,
        optimized_prompt: str,
        analysis: PromptAnalysis,
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO prompt_versions
                    (original_prompt, optimized_prompt, analysis_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    original_prompt,
                    optimized_prompt,
                    analysis.model_dump_json(),
                    datetime.now(UTC).isoformat(),
                ),
            )
            version_id = cursor.lastrowid
            if version_id is None:
                raise RuntimeError("保存版本失败。")
            return int(version_id)

    def list_versions(self) -> list[VersionSummary]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, original_prompt, optimized_prompt, analysis_json, created_at
                FROM prompt_versions
                ORDER BY id DESC
                """
            ).fetchall()
        return [self._summary_from_row(row) for row in rows]

    def get_version(self, version_id: int) -> PromptVersion:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, original_prompt, optimized_prompt, analysis_json, created_at
                FROM prompt_versions
                WHERE id = ?
                """,
                (version_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"未找到版本：{version_id}")
        return self._version_from_row(row)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS prompt_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_prompt TEXT NOT NULL,
                    optimized_prompt TEXT NOT NULL,
                    analysis_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _summary_from_row(row: sqlite3.Row) -> VersionSummary:
        analysis = PromptAnalysis.model_validate(json.loads(row["analysis_json"]))
        return VersionSummary(
            id=int(row["id"]),
            original_preview=row["original_prompt"][:80],
            optimized_preview=row["optimized_prompt"][:80],
            score=analysis.score.total_score,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @staticmethod
    def _version_from_row(row: sqlite3.Row) -> PromptVersion:
        analysis = PromptAnalysis.model_validate(json.loads(row["analysis_json"]))
        return PromptVersion(
            id=int(row["id"]),
            original_prompt=row["original_prompt"],
            optimized_prompt=row["optimized_prompt"],
            analysis=analysis,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
