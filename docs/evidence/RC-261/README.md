# RC-261 Evidence

<!-- RC ID: RC-261 -->

## Scope

Validated high-frequency keyboard, focus, session, and diff-review workflows.
The work fixed two observed frictions: the settings page advertised `Ctrl+K`
without an implementation, and starting a new task session retained the prior
session's Composer draft.

## Efficiency Checkpoints

| Workflow | Before | After | Automated operation shape |
| --- | --- | --- | --- |
| Command palette | `Ctrl+K` had no UI response | Palette opens and focuses Search commands | 1 key chord, then 1 command click |
| Optimize and review | Shortcut path existed but was not covered with focus assertions | Default `Ctrl+Shift+O` and Vim `Alt+O` each create one request; closing the result restores focus to the star action | 1 key chord, 1 request, 1 close |
| Session switch | New session reset messages but retained old Composer draft | New session clears the draft and its local storage entry | 1 draft entry, 1 new-session action, 0 stale text |
| Diff review | File/hunk actions existed without one combined efficiency check | View original, accept hunk, run verification, and status feedback remain keyboard reachable | 3 review actions, explicit status checks |

The focused test file completed in 425 ms locally. This is an automation wall
time, not a human task-time claim or a substitute for a recruited high-frequency
user baseline.

## Verification

- `npm run test -- --run tests/Rc261Efficiency.test.tsx`: 4 passed.
- Combined RC-259/260/261 and related App/Task/Review regression: 34 passed.
- `npm run lint`: passed.
- `npm run build`: passed; Vite retained the existing single-chunk size warning.
- Playwright session `rc260` opened the command palette with `Ctrl+K`, focused
  its search input, saved `output/playwright/rc261-command-palette.png`, and
  reported 0 error-level console messages.

## External Limits

- No recruited high-frequency users or moderated operation-count baseline were
  available in this shared coding session; human efficiency and verbal
  confusion remain pending external UX validation.
- Native Tauri focus behavior, screen-reader traversal, and multi-window session
switching remain platform/release checks.

## RC-230~271 remediation follow-up (2026-07-19)

Agents navigation now uses `frontend/src/navigation.tsx`. Internal links share
one same-origin `NavigationProvider`; former `/prompt-management`, `/evaluations`,
and `/prompt-chaining` paths canonicalize once to Agents routes, while browser
back/forward remains driven by `popstate`. The focused navigation contract and
the full frontend suite pass 150 tests. Vite 8 vendor chunking reduces the
largest JavaScript chunk to about 202 KB.
