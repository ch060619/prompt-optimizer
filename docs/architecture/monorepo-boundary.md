# RC-056 Monorepo Boundary

- RC ID: RC-056
- Workspace manifest: `workspace.toml`
- Root task entry: `python scripts/workspace.py <install|check|test|build|verify>`

## Members

The workspace names the future desktop, CLI, Agent Core, protocol, and UI boundaries while
preserving the already validated implementation paths:

| Boundary | Current implementation | Ownership |
| --- | --- | --- |
| `apps/desktop` | Reserved | Desktop shell and OS integration only |
| `apps/cli` | `backend/src/prompt_optimizer/cli` | CLI/TUI commands and presentation |
| `backend/rabbit_code` | Reserved | Shared Agent Core migration target |
| `backend` | `backend/src/prompt_optimizer` | Current FastAPI, optimization, Provider, storage, and CLI compatibility code |
| `packages/protocol` | Reserved | Versioned cross-surface schemas |
| `packages/ui` | Reserved | Shared React primitives and tokens |
| `frontend` | `frontend/src` | Current React/Vite product surface |
| `scripts` | `scripts` | Repository checks and root tasks |
| `tests` | Reserved | Cross-member contracts |
| `docs` | `docs` | Plans, evidence, architecture, and governance |

Moving validated code is intentionally deferred. The manifest and task runner provide one root
entry point now; later RCs can migrate one boundary at a time while each commit remains buildable.

## Dependency Direction

The current check rejects backend/script imports from `frontend`, `apps`, or `packages`. Backend
business logic does not import UI code, and frontend builds against the App Server API boundary.
The protocol package is reserved for the versioned schemas defined in RC-061, so no speculative
cross-package import is added in RC-056.

## Verification

From the repository root:

```powershell
python scripts/workspace.py check
python scripts/workspace.py test
python scripts/workspace.py build
```

`check` validates all declared members, the unified `3.0.0` version in the manifest/backend/
frontend/lockfile, traceability, delivery-plan invariants, and current import boundaries.
