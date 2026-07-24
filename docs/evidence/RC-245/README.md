# RC-245 Evidence

RC ID: RC-245

## Scope

Agent events have a stable dictionary representation for CLI resume and GUI
rendering. Unknown event names safely degrade to `TERMINAL` instead of breaking
replay, while known tool, text, diff, and terminal events retain their payload.

## Verification

```text
.venv\\Scripts\\python.exe -m pytest backend/tests/test_rc245_cross_surface.py -q
```

Result: `2 passed`.

## Limits

The test covers the shared event boundary and local replay. A packaged native GUI
and a live terminal session remain platform-level verification items.
