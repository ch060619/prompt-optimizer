# ADR-0011：窗口与系统集成策略

- RC ID: RC-120
- Status: Accepted for the current webview boundary; native shell items pending
- Date: 2026-07-18
- Deciders: Rabbit Code engineering

## Decision

Rabbit Code uses one native window per process. Multiple workspaces remain internal routes and
sessions in that window; multi-window support is not part of the current boundary. The frontend
persists webview-facing window bounds, active inspector panel, inspector visibility, theme,
notification preference and optional tray preference under
`rabbit_code_window_preferences`.

Window bounds are stored in logical pixels. A desktop shell may read the record at startup and
must clamp it to the current work area with at least 80 pixels visible after a monitor change.
The browser implementation records `outerWidth`, `outerHeight`, `screenX` and `screenY` on resize
and unload; it does not claim permission to move a native window.

Light and dark themes are applied through the root `data-theme` attribute and CSS tokens. User
notifications use an in-app `rabbit-code:notification` event and the browser Notification API
only when permission was already granted. The optional tray setting is persisted but remains
inactive until the desktop shell implements the allowlisted `notify`/window bridge.

## Consequences

- Restart and monitor recovery are deterministic at the preference layer and testable without a
  Tauri runtime.
- Task inspector layout and appearance choices survive navigation and process reloads that share
  the local preference store.
- Native window restoration, tray lifecycle, OS notification permission prompts, DPI scaling and
  Windows/Linux multi-monitor behavior require a real desktop shell and remain pending.

## Verification

- `frontend/tests/WindowPreferences.test.ts` covers persistence, malformed/default-safe state,
  off-screen bounds clamping and notification suppression.
- `frontend/tests/TaskWorkspace.test.tsx` covers panel persistence through the task workspace.
- `frontend/tests/Settings.test.tsx` covers workspace theme persistence and the root theme hook.
- `scripts/check_desktop_boundary.py` remains the shell boundary gate; no Agent or Provider logic
  is added to `apps/desktop`.
