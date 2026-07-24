#!/usr/bin/env python3
"""RC-217: validate the versioned Provider privacy catalog without network access."""

from __future__ import annotations

from urllib.parse import urlsplit

from prompt_optimizer.providers import PRESETS

EXPECTED_POLICY_HOSTS = {
    "openrouter": {"openrouter.ai"},
    "deepseek": {"cdn.deepseek.com"},
    "moonshot": {"www.moonshot.cn"},
    "qwen": {"www.alibabacloud.com"},
    "doubao": {"www.volcengine.com"},
    "zhipu": {"www.bigmodel.cn"},
    "siliconflow": {"www.siliconflow.cn"},
    "groq": {"groq.com"},
    "together": {"www.together.ai"},
    "ollama": {"ollama.com"},
    "lmstudio": {"lmstudio.ai"},
}


def validate() -> list[str]:
    errors: list[str] = []
    for provider_id, preset in PRESETS.items():
        privacy = preset.privacy
        if privacy is None:
            errors.append(f"{provider_id}: missing privacy metadata")
            continue
        if privacy.version != "rc217-v1":
            errors.append(f"{provider_id}: unexpected privacy version")
        if not privacy.request_fields:
            errors.append(f"{provider_id}: request_fields must not be empty")
        if not privacy.service_region.strip():
            errors.append(f"{provider_id}: service_region must not be empty")
        parsed = urlsplit(privacy.privacy_policy_url)
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append(f"{provider_id}: policy URL must be HTTPS")
        elif parsed.hostname not in EXPECTED_POLICY_HOSTS.get(provider_id, set()):
            errors.append(f"{provider_id}: policy URL host is not an official host")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Provider privacy catalog is valid: {len(PRESETS)} presets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
