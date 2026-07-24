# RC-233 Evidence

## Scope

Added `backend/tests/test_rc233_cli.py` for text/JSON/JSONL output, interactive TTY and
non-TTY stdin, non-interactive permission policy, stable runtime/permission/cancel exit
codes, continue/resume session arguments, dry-run output, terminal capability reporting,
and a real Python subprocess smoke with no prompt or ANSI pollution.

## Verification

```text
python -m pytest backend/tests/test_rc233_cli.py -q
.venv\Scripts\ruff.exe check backend/tests/test_rc233_cli.py
```

Result: `11 passed`.

Static check result: `All checks passed!`.

## Limits

Linux shell execution and native interactive terminal attachment are capability-gated on
this Windows host; unavailable surfaces are reported rather than claimed as tested.
