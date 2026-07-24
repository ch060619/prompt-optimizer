# Rabbit Code GitHub Repository Setup

## Repository Topics

The following GitHub Topics should be set on the repository:

```
prompt-engineering  llm  cli  desktop-app  tauri  offline-first
developer-tools  open-source  mit-license  fastapi  react  typescript
python  rust  code-review  ai-tools  local-first
```

## Repository Structure

```
prompt-optimizer/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # CI: backend + frontend + docker + license-scan
│   │   └── release.yml         # Release: tag-triggered, multi-platform
│   ├── CODEOWNERS              # Sensitive path review rules
│   └── ISSUE_TEMPLATE/
├── apps/
│   └── desktop/
│       └── src-tauri/          # Tauri desktop shell (Rust)
├── backend/
│   ├── src/prompt_optimizer/   # Python backend (FastAPI)
│   ├── migrations/             # SQLite migrations
│   └── tests/                  # Backend tests
├── frontend/
│   ├── src/                    # React frontend
│   └── package.json
├── docs/
│   ├── adr/                    # Architecture Decision Records
│   ├── evidence/               # RC completion evidence
│   ├── legal/                  # Legal documents
│   ├── licenses/               # License references
│   └── research/               # Research registers
├── scripts/                    # Build, check, and validation scripts
├── data/
│   └── models/                 # Model manifest
├── LICENSE                     # MIT
├── NOTICE                      # Attribution notices
├── THIRD_PARTY_NOTICES.md      # Auto-generated dependency list
├── CHANGELOG.md                # Versioned changelog
├── GOVERNANCE.md               # Maintainer policies
├── SECURITY.md                 # Security policy
├── CONTRIBUTING.md             # Contribution guide
└── README.md                   # Project overview
```

## Project Board

### Columns

1. **Backlog** — Unstarted issues
2. **In Progress** — Issues with assignee and branch
3. **Review** — PRs awaiting review
4. **Done** — Merged and closed

### Labels

| Label | Color | Description |
| --- | --- | --- |
| `bug` | #d73a4a | Something isn't working |
| `enhancement` | #a2eeef | New feature or request |
| `documentation` | #0075ca | Improvements or additions to docs |
| `good first issue` | #7057ff | Good for newcomers |
| `help wanted` | #008672 | Extra attention is needed |
| `security` | #b60205 | Security-related issue |
| `rc-item` | #fbca04 | Maps to a Rabbit Code RC item |
| `release-blocker` | #d93f0b | Blocks a release |

## Milestones

| Milestone | Target | Description |
| --- | --- | --- |
| `v3.0.0-stable` | 2026-08 | First stable release: all RC-001 through RC-310 complete |
| `v3.1.0` | 2026-10 | Post-stable improvements based on user feedback |
| `v3.2.0` | 2026-12 | macOS support evaluation (if demand exists) |

## Releases

### Release Process

1. Tag `vX.Y.Z` on `main` branch
2. Release workflow triggers automatically (see `.github/workflows/release.yml`)
3. Artifacts: CLI wheel, desktop installers, SBOM, checksums, release notes
4. Channel resolution: stable (tag), beta (tag with -beta), nightly (tag with -nightly)

### Release History

See [CHANGELOG.md](CHANGELOG.md) for the full release history.

## Public Roadmap

### Completed (v3.0.0)

- Offline-first prompt analysis and optimization
- CLI (pip), Web workstation, and Tauri desktop shell
- Multi-provider support (OpenAI, Anthropic, Gemini, Azure, Vertex, Bedrock)
- Local model on-demand download (Gemma, Qwen)
- Version history with SQLite storage
- Template library
- Evaluation framework
- Supply chain security (SBOM, reproducible builds, license scanning)

### In Progress

- First public release preparation (RC-288 through RC-310)
- Documentation review and polish
- Clean environment verification

### Future

- macOS support (based on demand)
- Additional local model support
- Community-contributed templates and presets
- Plugin system evaluation
