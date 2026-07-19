from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from prompt_optimizer.artifact_manifest import ArtifactManifest, ArtifactVerificationError

# RC IDs: RC-188, RC-192. Keep a versioned, weight-free model manifest and explicit download policy.

_HASH = re.compile(r"^[0-9a-f]{64}$")


class ModelManifestError(ValueError):
    """Raised when the controlled model manifest is invalid."""


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    family: str
    source_url: str
    revision: str
    file_sha256: str
    parameters_billions: float
    quantization: str
    context_length: int
    disk_bytes: int
    ram_bytes: int
    vram_bytes: int
    chat_template: str
    chat_template_status: str
    eos_token: str
    model_card_status: str
    license_spdx: str
    license_url: str
    license_status: str
    license_constraints: str
    license_version: str
    gated: bool
    user_confirmation_required: bool
    distribution: str

    def to_artifact_manifest(self) -> ArtifactManifest:
        return ArtifactManifest(
            kind="model",
            name=self.model_id,
            version=self.revision,
            source_url=self.source_url,
            sha256=self.file_sha256,
            license_id=self.license_spdx,
            license_url=self.license_url,
            license_version=self.license_version,
            license_summary=self.license_constraints,
        )


@dataclass(frozen=True)
class HardwareCapacity:
    ram_bytes: int | None = None
    disk_free_bytes: int | None = None
    vram_bytes: int | None = None


@dataclass(frozen=True)
class ModelRecommendation:
    model_id: str
    recommended: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "recommended": self.recommended,
            "reasons": list(self.reasons),
        }


def load_manifest(path: Path) -> tuple[ModelSpec, ...]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ModelManifestError(f"cannot read model manifest: {path}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ModelManifestError("model manifest schema_version must be 1")
    if payload.get("rc_id") != "RC-188":
        raise ModelManifestError("model manifest rc_id must be RC-188")
    models = payload.get("models")
    if not isinstance(models, list) or not models:
        raise ModelManifestError("model manifest must contain models")
    return tuple(_parse_model(item) for item in models)


def recommend_models(
    models: tuple[ModelSpec, ...],
    capacity: HardwareCapacity,
    *,
    safety_margin: float = 0.8,
) -> tuple[ModelRecommendation, ...]:
    if not 0 < safety_margin <= 1:
        raise ValueError("safety_margin must be greater than 0 and at most 1")
    recommendations: list[ModelRecommendation] = []
    for model in models:
        reasons: list[str] = []
        if capacity.ram_bytes is not None and model.ram_bytes > capacity.ram_bytes * safety_margin:
            reasons.append("ram_exceeds_safe_margin")
        if (
            capacity.disk_free_bytes is not None
            and model.disk_bytes > capacity.disk_free_bytes * safety_margin
        ):
            reasons.append("disk_exceeds_safe_margin")
        if (
            capacity.vram_bytes is not None
            and model.vram_bytes > capacity.vram_bytes * safety_margin
        ):
            reasons.append("vram_exceeds_safe_margin")
        if model.user_confirmation_required:
            reasons.append("license_confirmation_required")
        recommendations.append(
            ModelRecommendation(
                model.model_id,
                not any(reason.endswith("safe_margin") for reason in reasons),
                tuple(reasons),
            )
        )
    return tuple(recommendations)


def is_known_model(model_id: str, models: tuple[ModelSpec, ...], *, advanced: bool = False) -> bool:
    return advanced or any(model.model_id == model_id for model in models)


def license_prompt(model: ModelSpec) -> dict[str, object]:
    """Return the non-secret information the UI must show before download."""
    return {
        "model_id": model.model_id,
        "distribution": model.distribution,
        "summary": model.license_constraints,
        "license_url": model.license_url,
        "license_version": model.license_version,
        "confirmation_required": model.user_confirmation_required,
    }


def validate_license_confirmation(
    model: ModelSpec,
    *,
    accepted: bool,
    confirmation_version: str | None,
) -> None:
    """Require the user to confirm the exact manifest license version before download."""
    if not model.user_confirmation_required:
        return
    if not accepted:
        raise ModelManifestError("model license must be accepted before download")
    if confirmation_version != model.license_version:
        raise ModelManifestError("license confirmation version does not match the manifest")


def qwen_coder_model(models: tuple[ModelSpec, ...]) -> ModelSpec:
    matches = [
        model
        for model in models
        if model.family == "Qwen2.5-Coder" and model.model_id.startswith("Qwen/Qwen2.5-Coder-")
    ]
    if len(matches) != 1:
        raise ModelManifestError("manifest must contain exactly one controlled Qwen2.5-Coder model")
    return matches[0]


def gemma_model(models: tuple[ModelSpec, ...]) -> ModelSpec:
    matches = [
        model
        for model in models
        if model.family == "Gemma" and model.model_id.startswith("google/gemma-3-")
    ]
    if len(matches) != 1:
        raise ModelManifestError("manifest must contain exactly one controlled Gemma 3 model")
    return matches[0]


def _parse_model(value: object) -> ModelSpec:
    if not isinstance(value, dict):
        raise ModelManifestError("each model entry must be an object")
    required = (
        "model_id",
        "family",
        "source_url",
        "revision",
        "file_sha256",
        "parameters_billions",
        "quantization",
        "context_length",
        "disk_bytes",
        "ram_bytes",
        "vram_bytes",
        "chat_template",
        "chat_template_status",
        "eos_token",
        "model_card_status",
        "license_spdx",
        "license_url",
        "license_status",
        "license_constraints",
        "license_version",
        "gated",
        "user_confirmation_required",
        "distribution",
    )
    if any(key not in value for key in required):
        raise ModelManifestError("model entry is missing required fields")
    model_id = _string(value, "model_id")
    file_sha256 = _string(value, "file_sha256")
    revision = _string(value, "revision")
    if not model_id or any(character.isspace() for character in model_id):
        raise ModelManifestError(f"invalid model_id: {model_id!r}")
    if not _HASH.fullmatch(file_sha256) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ModelManifestError(f"invalid fixed hash for model: {model_id}")
    if not _string(value, "source_url").startswith("https://"):
        raise ModelManifestError(f"model source must use HTTPS: {model_id}")
    positive_ints = ("context_length", "disk_bytes", "ram_bytes", "vram_bytes")
    for key in positive_ints:
        if not isinstance(value[key], int) or value[key] <= 0:
            raise ModelManifestError(f"{key} must be a positive integer: {model_id}")
    parameters = value["parameters_billions"]
    if not isinstance(parameters, (float, int)) or parameters <= 0:
        raise ModelManifestError(f"parameters_billions must be positive: {model_id}")
    if not isinstance(value["gated"], bool) or not isinstance(
        value["user_confirmation_required"], bool
    ):
        raise ModelManifestError(f"gated flags must be boolean: {model_id}")
    distribution = _string(value, "distribution")
    if distribution not in {"bundled", "ondemand", "manual"}:
        raise ModelManifestError(f"invalid distribution policy: {model_id}")
    if distribution == "bundled" and value["user_confirmation_required"]:
        raise ModelManifestError(
            f"bundled model cannot require a download confirmation: {model_id}"
        )
    model = ModelSpec(
        model_id=model_id,
        family=_string(value, "family"),
        source_url=_string(value, "source_url"),
        revision=revision,
        file_sha256=file_sha256,
        parameters_billions=float(parameters),
        quantization=_string(value, "quantization"),
        context_length=value["context_length"],
        disk_bytes=value["disk_bytes"],
        ram_bytes=value["ram_bytes"],
        vram_bytes=value["vram_bytes"],
        chat_template=_string(value, "chat_template"),
        chat_template_status=_string(value, "chat_template_status"),
        eos_token=_string(value, "eos_token"),
        model_card_status=_string(value, "model_card_status"),
        license_spdx=_string(value, "license_spdx"),
        license_url=_string(value, "license_url"),
        license_status=_string(value, "license_status"),
        license_constraints=_string(value, "license_constraints"),
        license_version=_string(value, "license_version"),
        gated=value["gated"],
        user_confirmation_required=value["user_confirmation_required"],
        distribution=distribution,
    )
    try:
        model.to_artifact_manifest()
    except ArtifactVerificationError as exc:
        raise ModelManifestError(str(exc)) from exc
    return model


def _string(value: dict[str, Any], key: str) -> str:
    item = value[key]
    if not isinstance(item, str) or not item.strip():
        raise ModelManifestError(f"{key} must be a non-empty string")
    return item.strip()
