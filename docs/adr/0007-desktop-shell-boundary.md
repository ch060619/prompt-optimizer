# ADR-0007：桌面壳职责和命令白名单

- RC ID: RC-060
- Status: Proposed；Tauri/Rust implementation and OS integration pending
- Date: 2026-07-17

## Boundary

`apps/desktop` is limited to window lifecycle, native file selection, notifications, update
metadata, OS secret-store bridging, and App Server sidecar lifecycle. The allowlist is stored in
`apps/desktop/command-allowlist.toml` and checked by `scripts/check_desktop_boundary.py`.

Agent state, Provider requests, prompts, sessions, permissions, and business workflows stay in the
App Server/Agent Core. The desktop shell may carry protocol messages but must not implement a
second Agent state machine or call a Provider directly.

## Pending Confirmation

No Tauri dependency or Rust project is introduced while the current environment lacks a validated
desktop build path. Windows/Linux packaging, OS Keychain behavior, sidecar crash handling, and
parameter-level Rust tests remain required before this ADR can move from Proposed to Accepted.
