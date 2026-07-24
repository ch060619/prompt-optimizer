# RC-234 Evidence

## Scope

Added `frontend/tests/Rc234Workflow.test.tsx` as a mocked App Server workflow suite.
It traces onboarding's API/local entries, Provider/models/review/settings route reachability,
and the workspace optimize -> compare -> adopt -> send flow. Existing focused suites remain
the detailed coverage for provider CRUD, local installation, diff actions, and settings.

The send regression is covered by `backend/tests/test_rc234_gui_send.py`. It reproduces a
second send after adopting an optimized prompt containing an output-format structure. The
offline path now reuses the service-owned protected structure instead of reparsing its
internal marker, while direct user-authored protected markers remain rejected.

## Verification

```text
npm test -- --run tests/Rc234Workflow.test.tsx
npm run lint
npm run build
```

Results: `2 passed`; ESLint and Vite build passed.

Backend focused verification:

```text
python -m pytest backend/tests/test_rc234_gui_send.py -q
python -m pytest backend/tests/test_evaluation.py backend/tests/test_rc158_evaluation.py backend/tests/test_rc234_gui_send.py backend/tests/test_rc142_structured_input.py -q
.venv\Scripts\ruff.exe check backend/src/prompt_optimizer/core/optimizer.py backend/src/prompt_optimizer/contracts.py backend/src/prompt_optimizer/providers/base.py backend/src/prompt_optimizer/providers/offline.py backend/src/prompt_optimizer/services.py backend/tests/test_rc142_structured_input.py backend/tests/test_rc234_gui_send.py
```

Results: `1 passed`; then `11 passed, 1 warning`; Ruff passed. The full backend suite
completed with `702 passed, 9 skipped, 2 warnings` before the traceability index was
regenerated after this checklist update.

## Browser smoke

The real-browser smoke used the local Vite/FastAPI services and completed optimize -> diff
-> adopt -> send. The final send status was `优化完成` with offline/local metadata and no
fallback error. Screenshot: `output/playwright/rc234-send-after-adopt.png`.

## Limits

No real cloud Provider request, local model weight download, native Tauri shell, or Linux
desktop run was performed in this Windows workspace.
