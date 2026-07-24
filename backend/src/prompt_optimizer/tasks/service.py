from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from prompt_optimizer.contracts import Storage
from prompt_optimizer.core.models import TaskKind, TaskRecord

# RC ID: RC-225. Reconcile durable tasks after an App Server restart.


class TaskService:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def create(
        self,
        *,
        owner_id: int,
        kind: TaskKind,
        input_json: dict[str, Any],
    ) -> TaskRecord:
        return self.storage.create_task(
            task_id=uuid.uuid4().hex,
            owner_id=owner_id,
            kind=kind,
            input_json=input_json,
        )

    def get(self, task_id: str, owner_id: int) -> TaskRecord:
        return self.storage.get_task(task_id, owner_id)

    def recover_incomplete(self) -> int:
        return self.storage.recover_incomplete_tasks()

    def run(self, task_id: str, owner_id: int, work: Callable[[], dict[str, Any]]) -> None:
        try:
            self.storage.update_task(task_id, owner_id, status="running")
            result = work()
        except Exception as exc:
            self.storage.update_task(task_id, owner_id, status="failed", error=str(exc))
            return
        self.storage.update_task(task_id, owner_id, status="succeeded", result_json=result)
