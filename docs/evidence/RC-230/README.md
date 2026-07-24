# RC-230 Evidence

## Scope

Added `backend/tests/test_rc230_agent_core.py` as an offline Agent Core quality suite.
It covers state transitions and terminal boundaries, the ToolRegistry call-loop building
block, preflight and mid-stream cancellation, idempotent model retry/replay, atomic budget
failure, context compression provenance, and durable checkpoint recovery/tamper rejection.

## Verification

Command:

```text
python -m pytest backend/tests/test_rc230_agent_core.py -q
```

Result: `8 passed`.

Static check:

```text
.venv\Scripts\ruff.exe check backend/tests/test_rc230_agent_core.py
```

Result: `All checks passed!`.

## Limits

The suite uses fake providers, local state, and temporary files. It does not call a real
Provider, runner, network, or external tool.
