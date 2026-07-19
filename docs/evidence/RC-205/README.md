# RC-205 Evidence

## Scope

Added security primitives for workspace path normalization, symlink/traversal
rejection, parameterized argv validation, shell syntax risk classification,
environment allowlisting, and immutable untrusted tool-output tagging.
ShellAdapter and ProcessManager now pass only filtered inherited/explicit
environment variables and use the shared argv validator. Tool output is marked
as data with `trusted=false`, `can_execute=false`, and an override marker;
repository or tool text cannot become permissions or system instructions.

## Verification

- `python -m pytest backend/tests/test_rc202_approval.py backend/tests/test_rc203_authorizations.py backend/tests/test_rc204_sandbox.py backend/tests/test_rc205_security.py backend/tests/test_rc091_shell_tools.py backend/tests/test_rc094_process_tools.py backend/tests/test_rc097_tool_registry.py backend/tests/test_rc201_capability_policy.py -q`: 41 passed, 4 skipped.
- `python -m ruff check` for security, shell, process, package exports, and RC-205 tests: passed.
- `python -m mypy --strict` for security, shell, and process modules: passed.

The tests cover traversal, symlink escape, NUL and shell-marker handling,
dangerous environment variables, prompt-injection text, and compatibility with
the existing shell/process boundaries.

## Residual limits

No real hostile repository, external command injection, or OS-level sandbox
escape was executed. Shell scripts remain an explicit high-risk operation and
continue through the existing permission/approval gate; broader sensitive-file
policy is RC-206.
