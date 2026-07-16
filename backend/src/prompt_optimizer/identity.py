from __future__ import annotations

import os
import warnings

# RC ID: RC-054. Centralize the Rabbit Code identity and legacy compatibility names.

PRODUCT_NAME = "Rabbit Code"
LEGACY_PRODUCT_NAME = "Prompt Optimizer"
DISTRIBUTION_NAME = "rabbit-code"
LEGACY_DISTRIBUTION_NAME = "prompt-optimizer"
CLI_NAME = "rabbit"
LEGACY_CLI_NAME = "prompt-opt"
LEGACY_COMPATIBILITY_CUTOFF = "3.0.0"


def compatible_env(suffix: str) -> str | None:
    new_name = f"RABBIT_CODE_{suffix}"
    legacy_name = f"PROMPT_OPTIMIZER_{suffix}"
    value = os.getenv(new_name)
    if value is not None:
        return value
    legacy_value = os.getenv(legacy_name)
    if legacy_value is not None:
        warnings.warn(
            f"{legacy_name} 已弃用，请迁移到 {new_name}；"
            f"兼容截止 Rabbit Code {LEGACY_COMPATIBILITY_CUTOFF}。",
            DeprecationWarning,
            stacklevel=2,
        )
    return legacy_value
