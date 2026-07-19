from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from backend.rabbit_code.plugins import (
    PluginRegistry,
    PluginStateError,
    PluginValidationError,
)

# RC ID: RC-077. Verify controlled plugin lifecycle, manifest checks, permissions, and uninstall.


def _package(tmp_path: Path, *, version: str = "1.0.0", **overrides: object) -> Path:
    package = tmp_path / f"package-{version}"
    package.mkdir()
    artifact = package / "plugin.py"
    artifact.write_text("controlled plugin artifact\n", encoding="utf-8")
    manifest = {
        "name": "sample",
        "version": version,
        "entrypoint": "sample.handler",
        "permissions": ["read"],
        "source": "local",
        "min_app_version": "3.0.0",
        "artifact": "plugin.py",
        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        **overrides,
    }
    (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return package


def test_example_plugin_can_install_enable_run_disable_and_uninstall(tmp_path: Path) -> None:
    package = _package(tmp_path)
    registry = PluginRegistry(
        tmp_path / "installed",
        handlers={"sample.handler": lambda context: context.payload["value"] + 1},
        allowed_permissions={"read"},
    )

    registry.install(package)
    registry.enable("sample")

    assert registry.execute("sample", {"value": 2}) == 3
    registry.disable("sample")
    with pytest.raises(PluginStateError, match="disabled"):
        registry.execute("sample", {"value": 2})
    registry.uninstall("sample")

    assert registry.list_plugins() == ()
    assert not (tmp_path / "installed" / "sample").exists()


def test_plugin_upgrade_replaces_previous_version_and_preserves_enabled_state(
    tmp_path: Path,
) -> None:
    registry = PluginRegistry(
        tmp_path / "installed",
        handlers={"sample.handler": lambda context: context.payload["version"]},
        allowed_permissions={"read"},
    )
    registry.install(_package(tmp_path, version="1.0.0"))
    registry.enable("sample")
    registry.upgrade(_package(tmp_path, version="1.1.0"))

    assert registry.get("sample").manifest.version == "1.1.0"
    assert registry.get("sample").enabled
    assert registry.execute("sample", {"version": "new"}) == "new"
    assert not (tmp_path / "installed" / "sample" / "1.0.0").exists()


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"source": "untrusted"}, "source"),
        ({"sha256": "0" * 64}, "hash"),
        ({"permissions": ["write"]}, "permission"),
        ({"min_app_version": "4.0.0"}, "compatible"),
    ],
)
def test_invalid_manifest_is_rejected_before_install(
    tmp_path: Path,
    overrides: dict[str, object],
    message: str,
) -> None:
    registry = PluginRegistry(tmp_path / "installed", allowed_permissions={"read"})

    with pytest.raises(PluginValidationError, match=message):
        registry.install(_package(tmp_path, **overrides))


def test_unknown_entrypoint_cannot_import_or_execute_arbitrary_code(tmp_path: Path) -> None:
    registry = PluginRegistry(tmp_path / "installed", handlers={})
    registry.install(_package(tmp_path, entrypoint="os.system"))

    with pytest.raises(PluginStateError, match="not registered"):
        registry.enable("sample")
