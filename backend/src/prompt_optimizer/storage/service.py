from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from prompt_optimizer.auth.service import AuthService
from prompt_optimizer.core.models import (
    ProjectSpace,
    PromptAnalysis,
    PromptVersion,
    TaskKind,
    TaskRecord,
    TaskStatus,
    UserPublic,
    VersionSummary,
)
from prompt_optimizer.identity import compatible_env
from prompt_optimizer.paths import default_db_path
from prompt_optimizer.storage.backup import BackupResult, backup_database, read_schema_version

# RC ID: RC-054. Prefer Rabbit Code configuration with a legacy fallback.

DEMO_USERNAME = "demo"
DEMO_PASSWORD_HASH = AuthService().hash_password("demo-password", "demo-salt")
DEFAULT_PROJECT_NAME = "默认项目"
SCHEMA_VERSION = 1


class StorageService:
    def __init__(
        self,
        db_path: Path | None = None,
        backup_dir: Path | None = None,
        config_path: Path | None = None,
    ) -> None:
        self.db_path = db_path or default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir = backup_dir or self.db_path.parent / "backups"
        configured_path = config_path or compatible_env("CONFIG")
        self.config_path = Path(configured_path).expanduser() if configured_path else None
        self.last_backup: BackupResult | None = None
        self._backup_before_migration()
        self._init_db()

    def save_version(
        self,
        original_prompt: str,
        optimized_prompt: str,
        analysis: PromptAnalysis,
        owner_id: int = 1,
        project_id: int | None = None,
    ) -> int:
        project_id = project_id or self.ensure_default_project(owner_id).id
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO prompt_versions
                    (
                        owner_id,
                        project_id,
                        original_prompt,
                        optimized_prompt,
                        analysis_json,
                        created_at
                    )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    owner_id,
                    project_id,
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

    def list_versions(self, owner_id: int = 1) -> list[VersionSummary]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    owner_id,
                    project_id,
                    original_prompt,
                    optimized_prompt,
                    analysis_json,
                    created_at
                FROM prompt_versions
                WHERE owner_id = ?
                ORDER BY id DESC
                """,
                (owner_id,),
            ).fetchall()
        return [self._summary_from_row(row) for row in rows]

    def get_version(self, version_id: int, owner_id: int = 1) -> PromptVersion:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    owner_id,
                    project_id,
                    original_prompt,
                    optimized_prompt,
                    analysis_json,
                    created_at
                FROM prompt_versions
                WHERE id = ? AND owner_id = ?
                """,
                (version_id, owner_id),
            ).fetchone()
        if row is None:
            raise KeyError(f"未找到版本：{version_id}")
        return self._version_from_row(row)

    def create_user(self, username: str, password_hash: str) -> UserPublic:
        now = datetime.now(UTC).isoformat()
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO users (username, password_hash, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (username, password_hash, now),
                )
                user_id = cursor.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValueError("用户名已存在。") from exc
        if user_id is None:
            raise RuntimeError("创建用户失败。")
        user = UserPublic(
            id=int(user_id),
            username=username,
            created_at=datetime.fromisoformat(now),
        )
        self.ensure_default_project(user.id)
        return user

    def get_user_by_username(self, username: str) -> tuple[UserPublic, str] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, username, password_hash, created_at
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()
        if row is None:
            return None
        return (
            UserPublic(
                id=int(row["id"]),
                username=row["username"],
                created_at=datetime.fromisoformat(row["created_at"]),
            ),
            row["password_hash"],
        )

    def get_user(self, user_id: int) -> UserPublic:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, username, created_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            raise KeyError("用户不存在。")
        return UserPublic(
            id=int(row["id"]),
            username=row["username"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def ensure_demo_user(self) -> UserPublic:
        found = self.get_user_by_username(DEMO_USERNAME)
        if found:
            return found[0]
        return self.create_user(DEMO_USERNAME, DEMO_PASSWORD_HASH)

    def ensure_default_project(self, owner_id: int) -> ProjectSpace:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, owner_id, name, created_at
                FROM project_spaces
                WHERE owner_id = ?
                ORDER BY id
                LIMIT 1
                """,
                (owner_id,),
            ).fetchone()
            if row is None:
                now = datetime.now(UTC).isoformat()
                cursor = connection.execute(
                    """
                    INSERT INTO project_spaces (owner_id, name, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (owner_id, DEFAULT_PROJECT_NAME, now),
                )
                project_id = cursor.lastrowid
                if project_id is None:
                    raise RuntimeError("创建项目空间失败。")
                return ProjectSpace(
                    id=int(project_id),
                    owner_id=owner_id,
                    name=DEFAULT_PROJECT_NAME,
                    created_at=datetime.fromisoformat(now),
                )
        return ProjectSpace(
            id=int(row["id"]),
            owner_id=int(row["owner_id"]),
            name=row["name"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def list_project_spaces(self, owner_id: int) -> list[ProjectSpace]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, owner_id, name, created_at
                FROM project_spaces
                WHERE owner_id = ?
                ORDER BY id
                """,
                (owner_id,),
            ).fetchall()
        return [
            ProjectSpace(
                id=int(row["id"]),
                owner_id=int(row["owner_id"]),
                name=row["name"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def create_task(
        self,
        *,
        task_id: str,
        owner_id: int,
        kind: TaskKind,
        input_json: dict[str, object],
    ) -> TaskRecord:
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tasks
                    (
                        id,
                        owner_id,
                        kind,
                        status,
                        input_json,
                        result_json,
                        error,
                        created_at,
                        updated_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    owner_id,
                    kind,
                    "queued",
                    json.dumps(input_json, ensure_ascii=False),
                    None,
                    None,
                    now,
                    now,
                ),
            )
        return self.get_task(task_id, owner_id)

    def update_task(
        self,
        task_id: str,
        owner_id: int,
        *,
        status: TaskStatus,
        result_json: dict[str, object] | None = None,
        error: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE tasks
                SET status = ?, result_json = ?, error = ?, updated_at = ?
                WHERE id = ? AND owner_id = ?
                """,
                (
                    status,
                    (
                        json.dumps(result_json, ensure_ascii=False)
                        if result_json is not None
                        else None
                    ),
                    error,
                    datetime.now(UTC).isoformat(),
                    task_id,
                    owner_id,
                ),
            )

    def get_task(self, task_id: str, owner_id: int) -> TaskRecord:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    owner_id,
                    kind,
                    status,
                    input_json,
                    result_json,
                    error,
                    created_at,
                    updated_at
                FROM tasks
                WHERE id = ? AND owner_id = ?
                """,
                (task_id, owner_id),
            ).fetchone()
        if row is None:
            raise KeyError(f"未找到任务：{task_id}")
        return TaskRecord(
            id=row["id"],
            owner_id=int(row["owner_id"]),
            kind=row["kind"],
            status=row["status"],
            input_json=json.loads(row["input_json"]),
            result_json=json.loads(row["result_json"]) if row["result_json"] else None,
            error=row["error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS project_spaces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(owner_id) REFERENCES users(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS prompt_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER NOT NULL DEFAULT 1,
                    project_id INTEGER,
                    original_prompt TEXT NOT NULL,
                    optimized_prompt TEXT NOT NULL,
                    analysis_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(owner_id) REFERENCES users(id),
                    FOREIGN KEY(project_id) REFERENCES project_spaces(id)
                )
                """
            )
            self._ensure_column(
                connection,
                "prompt_versions",
                "owner_id",
                "INTEGER NOT NULL DEFAULT 1",
            )
            self._ensure_column(connection, "prompt_versions", "project_id", "INTEGER")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_templates (
                    id TEXT PRIMARY KEY,
                    owner_id INTEGER NOT NULL DEFAULT 1,
                    project_id INTEGER,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(owner_id) REFERENCES users(id),
                    FOREIGN KEY(project_id) REFERENCES project_spaces(id)
                )
                """
            )
            self._ensure_column(
                connection,
                "user_templates",
                "owner_id",
                "INTEGER NOT NULL DEFAULT 1",
            )
            self._ensure_column(connection, "user_templates", "project_id", "INTEGER")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    owner_id INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(owner_id) REFERENCES users(id)
                )
                """
            )
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        demo = self.ensure_demo_user()
        default_project = self.ensure_default_project(demo.id)
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE prompt_versions
                SET owner_id = ?, project_id = COALESCE(project_id, ?)
                WHERE owner_id IS NULL OR owner_id = 1
                """,
                (demo.id, default_project.id),
            )

    def _backup_before_migration(self) -> None:
        if not self.db_path.exists():
            return
        current_version = read_schema_version(self.db_path)
        if current_version > SCHEMA_VERSION:
            raise RuntimeError(
                f"数据库版本 {current_version} 高于当前支持版本 {SCHEMA_VERSION}。"
            )
        if current_version < SCHEMA_VERSION:
            self.last_backup = backup_database(
                self.db_path,
                self.backup_dir,
                schema_version=current_version,
                target_schema_version=SCHEMA_VERSION,
                config_path=self.config_path,
            )

    @staticmethod
    def _ensure_column(
        connection: sqlite3.Connection,
        table_name: str,
        column_name: str,
        definition: str,
    ) -> None:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        if any(row["name"] == column_name for row in rows):
            return
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

    @staticmethod
    def _summary_from_row(row: sqlite3.Row) -> VersionSummary:
        analysis = PromptAnalysis.model_validate(json.loads(row["analysis_json"]))
        return VersionSummary(
            id=int(row["id"]),
            owner_id=int(row["owner_id"]),
            project_id=int(row["project_id"]) if row["project_id"] is not None else None,
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
            owner_id=int(row["owner_id"]),
            project_id=int(row["project_id"]) if row["project_id"] is not None else None,
            original_prompt=row["original_prompt"],
            optimized_prompt=row["optimized_prompt"],
            analysis=analysis,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
