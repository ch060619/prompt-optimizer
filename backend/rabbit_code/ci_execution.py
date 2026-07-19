from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

# RC ID: RC-104. Define explicit non-interactive terminal and permission policy boundaries.


class NonInteractiveError(ValueError):
    pass


class PermissionStrategy(StrEnum):
    DENY = "deny"
    READ_ONLY = "read-only"
    APPROVE = "approve"


@dataclass(frozen=True)
class NonInteractivePolicy:
    strategy: PermissionStrategy
    explicit: bool


def resolve_non_interactive_policy(
    *,
    stdin_is_tty: bool,
    force_non_interactive: bool,
    requested: str | None,
) -> NonInteractivePolicy | None:
    if not force_non_interactive and stdin_is_tty:
        return None
    if requested is None:
        if force_non_interactive:
            raise NonInteractiveError(
                "--non-interactive requires --permission-policy"
            )
        return NonInteractivePolicy(PermissionStrategy.READ_ONLY, explicit=False)
    try:
        strategy = PermissionStrategy(requested)
    except ValueError as exc:
        raise NonInteractiveError(f"unsupported permission policy: {requested}") from exc
    return NonInteractivePolicy(strategy, explicit=True)
