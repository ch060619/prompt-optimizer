# RC ID: RC-290. Post-release maintenance policy.

## Maintenance Policy

### Versioning

Rabbit Code follows Semantic Versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes (e.g., database schema migrations, CLI command removal)
- **MINOR**: New features (e.g., new provider adapter, new analysis rule)
- **PATCH**: Bug fixes and security patches

### Release Cadence

| Channel | Cadence | Stability |
| --- | --- | --- |
| Stable | Every 2-3 months | Production-ready |
| Beta | Every 2-4 weeks | Feature-complete, testing |
| Nightly | Every push to main | Experimental |

### Compatibility Policy

#### Python CLI

- Python 3.10+ supported
- Breaking changes require MAJOR version bump
- Database migrations are versioned (TARGET_SCHEMA_VERSION)
- Older databases are auto-migrated forward; rollback is blocked if schema is newer

#### Desktop (Tauri)

- Windows 10+ and Linux (Ubuntu 20.04+) supported
- macOS not supported (deferred to v3.2.0 based on demand)
- Desktop installer format may change between MAJOR versions

#### API (FastAPI)

- API versioning via `/api/v1/` prefix
- Breaking API changes require MAJOR version bump
- Non-breaking additions are allowed in MINOR versions

### Security Patch Policy

| Severity | Patch Timeline | Backport? |
| --- | --- | --- |
| Critical | 7 days | Yes, to last stable |
| High | 14 days | Yes, to last stable |
| Medium | 30 days | No |
| Low | Next release | No |

Security patches are released as PATCH versions (e.g., 3.0.1).

### Dependency Update Cadence

- **Dependabot**: Weekly checks for Python and npm dependencies
- **Major version updates**: Reviewed quarterly
- **Security updates**: Fast-tracked (bypass normal review for patch versions fixing CVEs)
- **License changes**: Any dependency license change triggers `scan_license_risks.py` review

### Deprecation Policy

1. Feature is marked deprecated in CHANGELOG.md and CLI help output.
2. Deprecation warning is shown for at least one MINOR version.
3. Feature is removed in the next MAJOR version.

### End of Life

- Each MAJOR version receives security patches for 6 months after the next MAJOR release.
- After EOL, users must upgrade to continue receiving security fixes.

### Community Support

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and community help
- Security Advisories: Private vulnerability reporting (see SECURITY.md)
- No commercial support is offered
