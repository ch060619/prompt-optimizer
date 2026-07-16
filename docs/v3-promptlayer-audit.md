# V3.0 PromptLayer Frontend Audit

Date: 2026-07-16
Branch: `v3.0-promptlayer-redesign`
Baseline: `v2.0-baseline` -> `8306d11`

## Reference review

`PromptLayer_网站视觉与前端实现审计.docx` was rendered through Microsoft Word because the
bundled LibreOffice renderer could not find `soffice` on this Windows host. The exported PDF has
115 pages, and all 115 pages were converted to PNGs and reviewed. The document contains 16 core
pages, 4 high-volume detail templates, 87 screenshot segments, interaction states, public frontend
implementation notes, and an appendix describing exclusions and template scale.

The visual and interaction requirements that directly affect this project are:

- cream paper surfaces (`#FAF5EB`, `#EEE9DF`) with dark stage/navigation (`#141413`)
- dark brown text (`#432C10`), gold action color (`#F5CF63`), muted text (`#87847F`), and 1px rules
- serif display typography paired with sans-serif UI typography
- 12-column desktop grid, 64px desktop gutter, 24px mobile gutter, and restrained radii
- shared activity strip, header, full-screen menu, footer, service status, CTA and link treatment
- product template rhythm: centered hero, stable product visual, 3x3 feature grid, split narrative,
  FAQ, and footer
- index/detail/legal variants with the same shell and a narrower reading measure where appropriate
- reveal motion around 1.2s with `power3.out`, character hover motion around 0.5s, FAQ grid expansion,
  250ms page transition, and reduced-motion fallbacks
- semantic HTML, `focus-visible`, keyboard navigation, stable image dimensions, and no horizontal overflow

The reference appendix also says that a derivative implementation should replace PromptLayer's
trademark, copy, customer logos, product screenshots, and illustration to avoid brand confusion.
This implementation therefore uses the current Prompt Optimizer's real features and data rather than
copying the reference site's marketing claims.

## Current project facts

| Area | Verified state |
| --- | --- |
| Frontend | React 18 + TypeScript + Vite 5 |
| Package manager | npm, locked by `frontend/package-lock.json` |
| Entry | `frontend/src/main.tsx` -> `frontend/src/App.tsx` |
| Routing | No router or route components; one SPA root at `/` |
| Shared shell | No shared Header, Footer, navigation, or layout component |
| Styling | One `frontend/src/styles.css` file with a utility-free three-column workbench |
| Assets | No tracked raster, vector, font, Lottie, or Canvas assets |
| Icons | `lucide-react` only |
| Motion | No GSAP, ScrollTrigger, Lenis, View Transitions, or reduced-motion code |
| API boundary | `frontend/src/api.ts` calls the FastAPI endpoints listed below |
| Backend | Python 3.12 + FastAPI, offline-first services, SQLite history |
| Authentication | JWT token in `localStorage` under `prompt_optimizer_token` |
| Business state | Prompt text, templates, analysis, optimization, stream output, tasks, versions, diff, export |

## Current route and target mapping

The current code has only `/`; the table distinguishes existing routes from planned client-side
views so the redesign does not claim that the V2.0 app already contains a marketing-site route tree.

| Current route or contract | Word target | Implementation boundary |
| --- | --- | --- |
| `/` | Home / platform overview | Keep the real prompt workspace reachable from the first screen and use the paper overview as the visual shell |
| `POST /api/analyze` | Evaluations product narrative | Preserve the analysis action and score breakdown |
| `POST /api/optimize`, `/api/optimize/stream` | Prompt Management product narrative | Preserve synchronous and SSE optimization flows |
| `GET /api/templates` | Prompt Management / templates index | Preserve category filtering and template selection |
| `GET /api/history`, `/api/history/{id}/diff/{other}` | Version/detail views | Preserve history, score deltas, and diff output |
| `POST /api/tasks/*`, `GET /api/tasks/*` | Background task and workflow views | Preserve optimize, export, and evaluate task status |
| `POST /api/export` | Workspace/export action | Preserve Markdown, JSON, TXT, and CSV downloads |
| No current route | Pricing, case studies, blog, contact, legal, model/glossary indexes and detail templates | Add only truthful, data-driven views based on README, docs, provider registry, templates, and local behavior; do not invent customer claims or unsupported backend contracts |

## Component and resource audit

`App.tsx` currently owns authentication, template loading, prompt editing, analysis, optimization,
SSE parsing callbacks, background task polling, history, diff, export, and all markup. The minimum
safe extraction boundary is:

- `AppShell`: activity strip, header, menu, route transition, and footer
- `PromptWorkspace`: existing prompt/API workflow, kept behaviorally equivalent
- `ProductPage`, `IndexPage`, `DetailPage`, `LegalPage`: data-driven visual templates
- `FAQ`, `CharacterLink`, `Reveal`, `ServiceStatus`, and `RabbitArtwork`: shared interactions/assets

Searches over tracked files found no `cake`, `cake.png`, `cake.jpg`, `cake.webp`, `background-image`,
`<img>`, `<picture>`, `<svg>`, `<canvas>`, Lottie, Next/Image, GSAP, ScrollTrigger, Lenis, View
Transitions, `prefers-reduced-motion`, or `focus-visible` references. Therefore there are no existing
cake reference locations to miss; the rabbit asset and every illustration reference introduced by V3.0
will be centralized and separately audited in stage 4.

## Baseline verification

Commands run before code changes:

- `npm ci` in `frontend`: passed
- `npm run lint`: passed
- `npm test`: passed, 5 tests
- `npx tsc --noEmit`: passed
- `npm run build`: passed
- `python -m pytest -q backend\\tests`: passed, 31 tests
- `python -m ruff check backend`: passed
- `python -m mypy backend\\src`: passed, 34 source files

The V3.0 backend was started from the V3.0 source at `127.0.0.1:8000` and Vite at
`127.0.0.1:5173`. Baseline Playwright screenshots were captured at 1440x900, 1024x768, and
390x844 under the thread visualization directory. The baseline console reported the pre-existing
`/favicon.ico` 404 and a password-field/form warning; later stages must remove both without
introducing new console errors.

## Stage 1 conclusion

The redesign can be implemented without changing backend endpoints, data models, authentication,
forms, or business workflows. The main risk is the current monolithic `App.tsx`; staged extraction
and template data are required so the visual shell can change independently from the existing API
state machine. The next stage is limited to the global visual foundation and shared shell.
