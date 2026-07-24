from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# RC ID: RC-166. Keep OpenAI-compatible service presets data-driven and auditable.


@dataclass(frozen=True)
class ProviderPrivacy:
    version: str
    execution_location: Literal["local", "cloud"]
    request_fields: tuple[str, ...]
    service_region: str
    privacy_policy_url: str
    retention_risk: str


@dataclass(frozen=True)
class ProviderPreset:
    id: str
    display_name: str
    base_url: str
    model_discovery_path: str
    compatibility: str
    limitations: str
    sensitive_headers: tuple[str, ...] = ()
    privacy: ProviderPrivacy | None = None


_CLOUD_REQUEST_FIELDS = (
    "prompt/messages",
    "selected model",
    "generation parameters",
    "tool definitions/results when enabled",
    "request metadata",
    "API credential in the transport header",
)
_LOCAL_REQUEST_FIELDS = (
    "prompt/messages",
    "selected model",
    "generation parameters",
    "tool definitions/results when enabled",
)
_CLOUD_RETENTION_RISK = (
    "Retention, training use, and deletion controls are not inferred here; "
    "verify the current official policy and account terms before sending sensitive data."
)
_LOCAL_RETENTION_RISK = (
    "Retention is controlled by the local environment; Rabbit Code does not send "
    "this route to a cloud service, and local server logs, OS storage, and loaded "
    "model behavior remain the user's responsibility."
)


def _cloud_privacy(url: str, region: str) -> ProviderPrivacy:
    return ProviderPrivacy(
        "rc217-v1",
        "cloud",
        _CLOUD_REQUEST_FIELDS,
        region,
        url,
        _CLOUD_RETENTION_RISK,
    )


def _local_privacy(url: str) -> ProviderPrivacy:
    return ProviderPrivacy(
        "rc217-v1",
        "local",
        _LOCAL_REQUEST_FIELDS,
        "Local machine / configured runner",
        url,
        _LOCAL_RETENTION_RISK,
    )


PRESETS: dict[str, ProviderPreset] = {
    "openrouter": ProviderPreset(
        "openrouter", "OpenRouter", "https://openrouter.ai/api/v1", "/models", "high",
        "Provider routing and model availability vary by upstream.",
        ("Authorization", "HTTP-Referer", "X-Title"),
        _cloud_privacy(
            "https://openrouter.ai/privacy",
            "Provider-defined; upstream routing may vary.",
        ),
    ),
    "deepseek": ProviderPreset(
        "deepseek", "DeepSeek", "https://api.deepseek.com/v1", "/models", "high",
        "Model IDs and feature availability are service-specific.",
        privacy=_cloud_privacy(
            "https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html",
            "Provider-defined; account and endpoint policy apply.",
        ),
    ),
    "moonshot": ProviderPreset(
        "moonshot", "Moonshot / Kimi", "https://api.moonshot.cn/v1", "/models", "high",
        "Context and model availability depend on the Kimi account region.",
        privacy=_cloud_privacy(
            "https://www.moonshot.cn/privacy-policy",
            "Account/region-defined; verify the selected endpoint.",
        ),
    ),
    "qwen": ProviderPreset(
        "qwen", "Qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1", "/models", "high",
        "DashScope model IDs and regional access apply.",
        privacy=_cloud_privacy(
            "https://www.alibabacloud.com/help/en/legal/latest/privacy-policy",
            "Account/region-defined; verify the selected DashScope endpoint.",
        ),
    ),
    "doubao": ProviderPreset(
        "doubao", "Doubao", "https://ark.cn-beijing.volces.com/api/v3", "/models", "medium",
        "Endpoint IDs and region selection are required by Ark.",
        privacy=_cloud_privacy(
            "https://www.volcengine.com/docs/6256/64902",
            "Endpoint/region-defined; verify the selected Ark deployment.",
        ),
    ),
    "zhipu": ProviderPreset(
        "zhipu", "Zhipu", "https://open.bigmodel.cn/api/paas/v4", "/models", "high",
        "Model IDs and tool support follow the Zhipu account plan.",
        privacy=_cloud_privacy(
            "https://www.bigmodel.cn/information/agreement/privacypolicy",
            "Provider-defined; account and endpoint policy apply.",
        ),
    ),
    "siliconflow": ProviderPreset(
        "siliconflow", "SiliconFlow", "https://api.siliconflow.cn/v1", "/models", "high",
        "The upstream model catalog controls context and tool support.",
        privacy=_cloud_privacy(
            "https://www.siliconflow.cn/privacypolicy",
            "Provider-defined; account and endpoint policy apply.",
        ),
    ),
    "groq": ProviderPreset(
        "groq", "Groq", "https://api.groq.com/openai/v1", "/models", "high",
        "Fast inference does not imply every OpenAI parameter is supported.",
        privacy=_cloud_privacy(
            "https://groq.com/privacy-policy/",
            "Provider-defined; account and endpoint policy apply.",
        ),
    ),
    "together": ProviderPreset(
        "together", "Together AI", "https://api.together.xyz/v1", "/models", "high",
        "Model-specific context and tool support apply.",
        privacy=_cloud_privacy(
            "https://www.together.ai/privacy",
            "Provider-defined; account and endpoint policy apply.",
        ),
    ),
    "ollama": ProviderPreset(
        "ollama", "Ollama", "http://127.0.0.1:11434/v1", "/models", "medium",
        "The local server must be running; model discovery is local-only.",
        privacy=_local_privacy("https://ollama.com/privacy"),
    ),
    "lmstudio": ProviderPreset(
        "lmstudio", "LM Studio", "http://127.0.0.1:1234/v1", "/models", "medium",
        "The local server and loaded model determine compatibility.",
        privacy=_local_privacy("https://lmstudio.ai/privacy-policy"),
    ),
}


def get_preset(provider_name: str) -> ProviderPreset | None:
    return PRESETS.get(provider_name.lower())
