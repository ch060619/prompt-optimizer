# RC-260 Evidence

<!-- RC ID: RC-260 -->

## Scope

Validated the no-tutorial first-run paths for the API and local routes, then
validated prompt optimization as a separate action from sending.

## Proxy Walkthrough

| Task | Result | Observation |
| --- | --- | --- |
| Discover both routes | PASS | The first-run page exposes `USE API / CONFIGURE PROVIDER` and `NO API / LOCAL MODEL` as direct choices with network, privacy, and hardware consequences. |
| Configure an API route | PASS WITH MOCK | The four-step flow names protocol, endpoint/credential, model, and test/default; it explicitly distinguishes a Provider API key from a Rabbit Code account password. `MOCK / $0` unlocks saving. |
| Install a local model | PASS WITH MOCK STATE | The six checkpoints are hardware, runner, model, license, install, and health. Qwen2.5-Coder was taken through resumable download, checksum verification, and local health confirmation without a remote Provider. |
| Optimize a prompt | PASS WITH MOCK | A real prompt enabled the star action, produced an editable preview, preserved the original input, and kept `SEND` as a separate action. |

This is one automated, no-instructions proxy walkthrough, not a human target
user study. It records observable friction and executable checkpoints without
claiming a completion rate or time-to-task for external participants.

## Verification

- `npm run test -- --run tests/Rc260Usability.test.tsx`: 4 passed.
- Playwright session `rc260` completed the API, local-model, and optimization
  checkpoints; the health endpoint and optimization responses were mocked.
- After the health mock was installed, Playwright reported 0 console errors and
  0 warnings for the onboarding page.
- Screenshots: `output/playwright/rc260/onboarding.png`,
  `output/playwright/rc260/local-install.png`, and
  `output/playwright/rc260/local-ready.png`.

## External Limits

- No external target users were available in this shared coding session, so
  completion rate, task time, error count, and verbal confusion remain pending
  moderated recruitment and re-test.
- The Vite-only development server did not provide the real App Server; no
  Provider request, model weight download, runner process, or hardware install
  was executed. These are platform/release acceptance checks.
