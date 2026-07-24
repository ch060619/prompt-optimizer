from __future__ import annotations

from scripts.check_rc241_ci_mock import main

# RC ID: RC-241. Keep ordinary CI deterministic and external-Provider free.


def test_ci_mock_policy_is_enabled() -> None:
    assert main() == 0
