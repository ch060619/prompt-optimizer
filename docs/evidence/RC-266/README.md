# RC-266 Evidence

<!-- RC ID: RC-266 -->

## Scope

Added `docs/user-guide.md` with the actual CLI command groups, GUI routes, composer, diamond-star optimization flow, session-local model selection, streaming/background work, history/diff/export, MCP, plugins, Hooks, and recovery paths.

## Verification

- `python scripts/check_docs.py --run`: passed.
- The GUI route list and star behavior were checked against `frontend/src/App.tsx` and `frontend/src/components/PromptOptimizeButton.tsx`.
- The example template command uses the existing `general-summary` template ID.

## Limits

The guide documents current UI behavior; MCP/plugin/Hooks controls remain permission-gated and do not imply that a third-party extension has been reviewed.
