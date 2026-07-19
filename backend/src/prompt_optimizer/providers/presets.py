from __future__ import annotations

from dataclasses import dataclass

# RC ID: RC-166. Keep OpenAI-compatible service presets data-driven and auditable.


@dataclass(frozen=True)
class ProviderPreset:
    id: str
    display_name: str
    base_url: str
    model_discovery_path: str
    compatibility: str
    limitations: str
    sensitive_headers: tuple[str, ...] = ()


PRESETS: dict[str, ProviderPreset] = {
    "openrouter": ProviderPreset(
        "openrouter", "OpenRouter", "https://openrouter.ai/api/v1", "/models", "high",
        "Provider routing and model availability vary by upstream.",
        ("Authorization", "HTTP-Referer", "X-Title"),
    ),
    "deepseek": ProviderPreset(
        "deepseek", "DeepSeek", "https://api.deepseek.com/v1", "/models", "high",
        "Model IDs and feature availability are service-specific.",
    ),
    "moonshot": ProviderPreset(
        "moonshot", "Moonshot / Kimi", "https://api.moonshot.cn/v1", "/models", "high",
        "Context and model availability depend on the Kimi account region.",
    ),
    "qwen": ProviderPreset(
        "qwen", "Qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1", "/models", "high",
        "DashScope model IDs and regional access apply.",
    ),
    "doubao": ProviderPreset(
        "doubao", "Doubao", "https://ark.cn-beijing.volces.com/api/v3", "/models", "medium",
        "Endpoint IDs and region selection are required by Ark.",
    ),
    "zhipu": ProviderPreset(
        "zhipu", "Zhipu", "https://open.bigmodel.cn/api/paas/v4", "/models", "high",
        "Model IDs and tool support follow the Zhipu account plan.",
    ),
    "siliconflow": ProviderPreset(
        "siliconflow", "SiliconFlow", "https://api.siliconflow.cn/v1", "/models", "high",
        "The upstream model catalog controls context and tool support.",
    ),
    "groq": ProviderPreset(
        "groq", "Groq", "https://api.groq.com/openai/v1", "/models", "high",
        "Fast inference does not imply every OpenAI parameter is supported.",
    ),
    "together": ProviderPreset(
        "together", "Together AI", "https://api.together.xyz/v1", "/models", "high",
        "Model-specific context and tool support apply.",
    ),
    "ollama": ProviderPreset(
        "ollama", "Ollama", "http://127.0.0.1:11434/v1", "/models", "medium",
        "The local server must be running; model discovery is local-only.",
    ),
    "lmstudio": ProviderPreset(
        "lmstudio", "LM Studio", "http://127.0.0.1:1234/v1", "/models", "medium",
        "The local server and loaded model determine compatibility.",
    ),
}


def get_preset(provider_name: str) -> ProviderPreset | None:
    return PRESETS.get(provider_name.lower())

