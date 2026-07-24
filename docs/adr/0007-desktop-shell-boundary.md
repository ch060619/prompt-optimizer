# ADR-0007：桌面壳职责和命令白名单

- RC ID: RC-060
- Status: Accepted；Tauri/Rust boundary verified on Windows and Linux
- Date: 2026-07-17

## Boundary

`apps/desktop` is limited to window lifecycle, native file selection, notifications, update
metadata, OS secret-store bridging, and App Server sidecar lifecycle. The allowlist is stored in
`apps/desktop/command-allowlist.toml` and checked by `scripts/check_desktop_boundary.py`.

Agent state, Provider requests, prompts, sessions, permissions, and business workflows stay in the
App Server/Agent Core. The desktop shell may carry protocol messages but must not implement a
second Agent state machine or call a Provider directly.

## Verification

The Tauri 2 project lives in `apps/desktop/src-tauri`. Windows and Linux `cargo check/build`
complete, and native-window probes create, resize, maximize and close the shell without leaving a
process behind. The static boundary checker ignores generated build output but continues to reject
Agent or Provider business logic in desktop source files. Packaging, OS Keychain round-trips and
sidecar artifact binding remain release/security integration work.
