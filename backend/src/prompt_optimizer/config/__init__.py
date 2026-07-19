"""Layered Rabbit Code configuration boundary."""

# RC IDs: RC-065, RC-181. Export the typed layered configuration service.

from prompt_optimizer.config.service import (
    CONFIG_FIELDS,
    ConfigField,
    ConfigReference,
    ConfigService,
    ConfigSnapshot,
    parse_config_reference,
)

__all__ = [
    "CONFIG_FIELDS",
    "ConfigField",
    "ConfigReference",
    "ConfigService",
    "ConfigSnapshot",
    "parse_config_reference",
]
