from __future__ import annotations

from scripts.check_rc242_ci_matrix import main

# RC ID: RC-242. Keep platform matrix coverage explicit and reviewable.


def test_ci_matrix_policy_is_valid() -> None:
    assert main() == 0
