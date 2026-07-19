# ADR-0012：标题栏方案待平台原型确认

- RC ID: RC-121
- Status: Proposed；pending Windows/Linux desktop prototypes
- Date: 2026-07-18
- Deciders: Rabbit Code engineering

## Decision Status

No native or custom title-bar option is accepted yet. The repository currently contains only the
desktop shell boundary and command allowlist; it does not contain a runnable Tauri/Rust shell or a
Linux desktop prototype. Choosing an option without those fixtures would turn unobserved behavior
into a false compatibility claim.

## Required Comparison Before Acceptance

Both options must be exercised on supported Windows and Linux environments:

- Native title bar: drag region, maximize/restore, double-click, system menu, scaling, high
  contrast, keyboard navigation and screen-reader naming.
- Custom title bar: the same matrix, plus proof that drag regions never cover buttons, links,
  inputs, menu controls or the resize affordance.

The selected option must record viewport sizes, DPI/scaling, theme, keyboard path, assistive
technology result and known limitations. The test fixture must be runnable without Agent or
Provider business logic in `apps/desktop`.

## Current Evidence

`scripts/check_desktop_boundary.py` passes and confirms that `apps/desktop` contains only the
allowlisted shell boundary. It cannot validate title-bar interaction. RC-121 therefore remains
unchecked until the missing platform prototypes and interaction matrix exist.
