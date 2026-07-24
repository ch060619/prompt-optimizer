# ADR-0012：采用原生标题栏

- RC ID: RC-121
- Status: Accepted
- Date: 2026-07-18
- Deciders: Rabbit Code engineering

## Decision Status

Rabbit Code uses the operating system title bar through Tauri `decorations: true`. A custom title
bar is rejected because it would add drag-region, resize, system-menu, scaling, high-contrast and
assistive-technology responsibilities without improving the coding workflow.

## Platform Evidence

- Windows native window: title `Rabbit Code`, initial 1551x1061, maximized 1721x1033, restored
  1551x1061, graceful close with exit code 0.
- Linux Docker/Xvfb/Openbox: initial 1534x999, resized 1200x800, EWMH-maximized 1536x1005,
  graceful close with exit code 0.
- Both Windows and Linux link the Tauri application from the same `tauri.conf.json` and React
  `frontend/dist` without Agent or Provider business logic in the shell.

## Current Evidence

`scripts/check_desktop_boundary.py` and RC-060 tests pass. The Linux interaction is reproducible
with `scripts/prototypes/rc121_linux_window_probe.sh`. Narrator/Orca reading remains a release-level
manual matrix; native decorations deliberately keep title-bar accessibility owned by the OS.
