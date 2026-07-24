# Changelog

All notable changes to Rabbit Code are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Channels

| Channel | Version Pattern | Stability | Rollout |
|---------|----------------|-----------|---------|
| **nightly** | `X.Y.Z-dev.YYYYMMDD` | Experimental | 10% |
| **beta** | `X.Y.0-beta.N` | Feature-complete, testing | 25% |
| **stable** | `X.Y.0` | Production-ready | 100% |

## [Unreleased]

### Added
- RC-272: Tauri desktop bundling enabled (Windows NSIS/MSI, Linux AppImage/deb/rpm)
- RC-273: CLI installation channels (PyPI, winget, Scoop, install scripts)
- RC-274: Reproducible packaging with PyInstaller sidecar spec
- RC-275: Local model on-demand download verified (no weights in installer)
- RC-276: Secure update check with HTTPS/hash verification, staged rollout, rollback
- RC-277: CycloneDX SBOM, build provenance, artifact hashes, license report
- RC-278: Release channel management (nightly/beta/stable) with migration gates

## [3.0.0] - 2026-07-22

### Added
- Cross-platform coding agent with terminal and desktop shared core
- Prompt optimization with rule/template/model composition
- Local model support with on-demand download
- Multi-provider cloud API support (OpenAI, Anthropic, Gemini, Azure, Vertex, Bedrock)
- Workspace isolation and data cleanup
- Offline rule-based optimization
- SQLite storage with versioned migrations
- FastAPI backend with streaming SSE support
- React frontend with Vite
- Tauri desktop shell

### Database Migration
- Schema version 2 (see `backend/src/prompt_optimizer/storage/migrations.py`)
- Migrations are forward-only; downgrade requires backup restore

### Breaking Changes from 2.x
- Configuration format updated (use `rabbit migrate-config` to upgrade)
- API response format standardized across all providers
- Local model manifest format updated
