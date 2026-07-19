from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.services import AppServices
from prompt_optimizer.sync import (
    OptionalSyncService,
    SyncAuthorizationError,
    SyncDisabledError,
)

# RC ID: RC-183. Verify local use remains independent from account and opt-in sync.


def test_offline_optimization_does_not_require_a_cloud_account() -> None:
    client = TestClient(create_app(AppServices()))

    response = client.post(
        "/api/v1/optimize",
        json={"prompt": "离线本地任务", "provider": "offline", "save_prompt_history": False},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["provider_used"] == "offline"


def test_sync_is_disabled_and_does_not_require_account_for_local_status() -> None:
    sync = OptionalSyncService()

    assert sync.status().local_only is True
    assert sync.status().account_required is False
    with pytest.raises(SyncDisabledError):
        sync.push({"local_profile": "kept-local"})


def test_enabling_sync_requires_separate_explicit_account_authorization() -> None:
    sync = OptionalSyncService(enabled=True, transport=None)

    assert sync.status().account_required is True
    with pytest.raises(SyncAuthorizationError):
        sync.push({"local_profile": "kept-local"})
