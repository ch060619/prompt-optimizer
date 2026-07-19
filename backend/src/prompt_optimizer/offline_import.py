from __future__ import annotations

import hashlib
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from prompt_optimizer.local_health import ResourceProbe, run_health_check
from prompt_optimizer.local_install import LocalInstallCore, LocalInstallError
from prompt_optimizer.model_manifest import (
    ModelManifestError,
    ModelSpec,
    load_manifest,
    validate_license_confirmation,
)
from prompt_optimizer.providers.runners import LocalRunnerAdapter, RunnerRegistry

# RC ID: RC-200. Import a weight-bearing offline package only after local validation.

DiskUsageReader = Callable[[Path], tuple[int, int, int]]


class OfflineImportError(RuntimeError):
    """Raised when an offline package is incomplete, unsafe, or invalid."""


@dataclass(frozen=True)
class OfflineImportResult:
    model_id: str
    version: str
    installed_path: str
    ready: bool
    state: dict[str, object]
    health_report: dict[str, object] | None

    def to_dict(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "version": self.version,
            "installed_path": self.installed_path,
            "ready": self.ready,
            "state": self.state,
            "health_report": self.health_report,
        }


class OfflineModelImporter:
    def __init__(
        self,
        target_root: Path,
        *,
        runner: LocalRunnerAdapter | None = None,
        runner_name: str = "ollama",
        disk_usage: DiskUsageReader = shutil.disk_usage,
        resource_probe: ResourceProbe | None = None,
    ) -> None:
        self.target_root = target_root.expanduser().resolve()
        self.runner = runner
        self.runner_name = runner_name
        self._disk_usage = disk_usage
        self._resource_probe = resource_probe

    def import_package(
        self,
        package_root: Path,
        *,
        model_id: str,
        license_accepted: bool,
        license_confirmation_version: str | None,
        expected_version: str | None = None,
    ) -> OfflineImportResult:
        package = package_root.expanduser().resolve()
        _manifest, model, source = self._validate_media(package, model_id)
        if expected_version is not None and expected_version != model.revision:
            raise OfflineImportError("offline package version does not match the manifest")
        try:
            validate_license_confirmation(
                model,
                accepted=license_accepted,
                confirmation_version=license_confirmation_version,
            )
        except ModelManifestError as exc:
            raise OfflineImportError(str(exc)) from exc
        self._check_disk(model)
        try:
            self.target_root.mkdir(parents=True, exist_ok=True)
            core = LocalInstallCore(self.target_root / safe_model_id(model.model_id))
            core.start(
                model_id=safe_model_id(model.model_id),
                runner=self.runner_name,
                source=source,
                checksum=model.file_sha256,
                license_accepted=True,
                version=model.revision,
                license_confirmation_version=license_confirmation_version,
                license_url=model.license_url,
                license_summary=model.license_constraints,
                health_check_required=True,
            )
            core.download_step(max_bytes=max(1, source.stat().st_size))
            core.verify()
            core.install()
        except (OSError, LocalInstallError) as exc:
            raise OfflineImportError(f"offline model installation failed: {exc}") from exc

        runner = self.runner or RunnerRegistry().create(self.runner_name)
        pulled = runner.pull(model.model_id)
        if pulled.status != "ok":
            raise OfflineImportError("offline model runner could not register the imported model")
        report = run_health_check(
            runner,
            model_id=model.model_id,
            context_length=model.context_length,
            report_path=core.root / "health-report.json",
            resource_probe=self._resource_probe,
            state_recorder=core,
        )
        state = core.state.to_dict() if core.state is not None else {}
        return OfflineImportResult(
            model_id=model.model_id,
            version=model.revision,
            installed_path=str(core.root / safe_model_id(model.model_id)),
            ready=report.ready,
            state=state,
            health_report=report.to_dict(),
        )

    def _validate_media(
        self,
        package: Path,
        model_id: str,
    ) -> tuple[dict[str, object], ModelSpec, Path]:
        manifest_path = package / "manifest.yml"
        dependencies = package / "dependencies"
        models = package / "models"
        if not package.is_dir() or not manifest_path.is_file():
            raise OfflineImportError("offline package manifest.yml is missing")
        if not dependencies.is_dir():
            raise OfflineImportError("offline package dependencies directory is missing")
        if not models.is_dir():
            raise OfflineImportError("offline package models directory is missing")
        try:
            parsed_models = load_manifest(manifest_path)
        except ModelManifestError as exc:
            raise OfflineImportError(f"offline package manifest is invalid: {exc}") from exc
        matching = [model for model in parsed_models if model.model_id == model_id]
        if len(matching) != 1:
            raise OfflineImportError("offline package does not contain the requested model")
        model = matching[0]
        source = models / model_filename(model.model_id, model.quantization)
        if not source.is_file() or source.is_symlink():
            raise OfflineImportError("offline package model file is missing or unsafe")
        if _sha256(source) != model.file_sha256:
            raise OfflineImportError("offline package model checksum mismatch")
        return {"manifest": str(manifest_path)}, model, source

    def _check_disk(self, model: ModelSpec) -> None:
        probe = self.target_root
        while not probe.exists() and probe != probe.parent:
            probe = probe.parent
        try:
            free = self._disk_usage(probe)[2]
        except OSError as exc:
            raise OfflineImportError("cannot inspect target disk space") from exc
        if free < model.disk_bytes:
            raise OfflineImportError("offline import does not have enough free space")


def safe_model_id(model_id: str) -> str:
    value = model_id.replace("/", "__")
    if not value or value in {".", ".."} or any(char in value for char in "\\\0"):
        raise OfflineImportError("offline model ID is unsafe")
    return value


def model_filename(model_id: str, quantization: str) -> str:
    suffix = "".join(char for char in quantization.lower() if char.isalnum() or char in {".", "-"})
    if not suffix:
        raise OfflineImportError("offline model quantization suffix is invalid")
    return f"{safe_model_id(model_id)}.{suffix}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
