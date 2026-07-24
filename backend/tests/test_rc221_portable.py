from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest
from backend.rabbit_code.sessions import SessionStore

from prompt_optimizer.core.models import PromptTemplate
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.export.portable import (
    PORTABLE_SCHEMA_VERSION,
    PortableBundleService,
    PortableFormatError,
)
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-221. Verify portable JSON/ZIP round-trips and hostile archive rejection.


def test_portable_json_round_trip_preserves_prompts_templates_sessions_and_safe_settings(
    tmp_path: Path,
) -> None:
    storage = StorageService(tmp_path / "portable.sqlite3")
    versions = VersionService(storage)
    analysis = Optimizer().optimize("写一个项目总结")
    version_id = versions.create("写一个项目总结", analysis.optimized_prompt or "", analysis)
    version = versions.get(version_id)
    session = SessionStore().create("alice", "Project summary", ("draft", "review"))
    template = PromptTemplate(
        id="summary",
        name="Summary",
        category="business",
        description="A summary template",
        tags=["summary"],
        template="Summarize {topic}",
        variables=["topic"],
        best_practices=["Be concise"],
    )
    service = PortableBundleService()

    exported = service.export_json(
        sessions=[session],
        prompts=[version],
        templates=[template],
        settings={"theme": "dark", "api_key": "sk-secret", "logLevel": "info"},
        workspace={"id": "alpha", "name": "Alpha"},
    )
    payload = json.loads(exported)

    assert payload["schema_version"] == PORTABLE_SCHEMA_VERSION
    assert payload["sessions"][0]["messages"][1]["content"] == "review"
    assert payload["prompts"][0]["original_prompt"] == "写一个项目总结"
    assert payload["templates"][0]["id"] == "summary"
    assert payload["settings"] == {"logLevel": "info", "theme": "dark"}
    assert "api_key" not in exported.decode("utf-8")
    imported = service.import_document(exported, conflict_strategy="replace")
    assert imported.model_dump(mode="json") == service.parse(exported).model_dump(mode="json")


def test_portable_zip_preview_reports_conflicts_and_skip_is_non_destructive() -> None:
    service = PortableBundleService()
    archive = service.export_zip(
        sessions=[{"id": "session-1", "title": "One", "messages": ["hello"]}],
        prompts=[{"id": "prompt-1", "original_prompt": "a", "optimized_prompt": "b"}],
        templates=[
            {
                "id": "template-1",
                "name": "One",
                "category": "general",
                "description": "",
                "template": "{input}",
            }
        ],
        settings={"theme": "light"},
    )

    preview = service.preview(
        archive,
        existing_ids={
            "sessions": {"session-1"},
            "prompts": {"prompt-1"},
            "messages": {"session-1:message:0"},
            "settings": {"theme"},
        },
    )
    imported = service.import_document(
        archive,
        existing_ids={
            "sessions": {"session-1"},
            "prompts": {"prompt-1"},
            "messages": {"session-1:message:0"},
            "settings": {"theme"},
        },
        conflict_strategy="skip",
    )

    assert preview.to_dict() == {
        "schema_version": PORTABLE_SCHEMA_VERSION,
        "counts": {"sessions": 1, "messages": 1, "prompts": 1, "templates": 1, "settings": 1},
        "conflicts": {
            "sessions": ["session-1"],
            "messages": ["session-1:message:0"],
            "prompts": ["prompt-1"],
            "settings": ["theme"],
        },
        "conflict_strategies": ["skip", "replace"],
    }
    assert imported.sessions == []
    assert imported.prompts == []
    assert len(imported.templates) == 1
    assert imported.settings == {}

    message_only = service.import_document(
        archive,
        existing_ids={"messages": {"session-1:message:0"}},
        conflict_strategy="skip",
    )
    assert message_only.sessions[0].messages == []


def test_portable_import_rejects_credentials_schema_and_zip_path_traversal() -> None:
    service = PortableBundleService()
    valid = service.export_json(settings={"theme": "light"})
    payload = json.loads(valid)
    payload["settings"]["api_key"] = "secret"
    with pytest.raises(PortableFormatError, match="credential"):
        service.parse(json.dumps(payload).encode("utf-8"))

    invalid_zip = io.BytesIO()
    with zipfile.ZipFile(invalid_zip, "w") as archive:
        archive.writestr("manifest.json", json.dumps({"schema_version": PORTABLE_SCHEMA_VERSION}))
        archive.writestr("../data.json", b"{}")
    with pytest.raises(PortableFormatError, match="path traversal"):
        service.parse(invalid_zip.getvalue())

    with pytest.raises(PortableFormatError, match="duplicate prompts"):
        service.build_document(
            prompts=[
                {"id": "same", "original_prompt": "a", "optimized_prompt": "b"},
                {"id": "same", "original_prompt": "c", "optimized_prompt": "d"},
            ]
        )
