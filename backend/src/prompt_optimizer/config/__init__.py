"""Layered Rabbit Code configuration boundary."""

# RC ID: RC-065. Export the typed layered configuration service.

from prompt_optimizer.config.service import (
    CONFIG_FIELDS,
    ConfigField,
    ConfigService,
    ConfigSnapshot,
)

__all__ = ["CONFIG_FIELDS", "ConfigField", "ConfigService", "ConfigSnapshot"]
