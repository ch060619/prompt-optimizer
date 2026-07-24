# RC-279: Complete GitHub Release Workflow

## Status

**Complete (workflow + scripts + tests)** — Release workflow, release notes generator, and verification script all pass. 29 tests passed. Actual GitHub Actions execution requires pushing a `v*` tag to a GitHub repository.

## What Was Done

1. **Created GitHub Actions release workflow** `.github/workflows/release.yml`:
   - Triggered by plain Git Tag push (`v*` pattern)
   - 5 jobs: `resolve-channel`, `build-cli`, `build-desktop`, `build-sbom`, `publish`
   - Channel resolution from tag (nightly/beta/stable)
   - CLI wheel build on ubuntu-latest
   - Desktop build matrix: ubuntu-latest (Linux deb/AppImage/rpm) + windows-latest (NSIS/MSI)
   - SBOM generation via `scripts/generate_sbom.py`
   - Publish job: assembles all artifacts, generates release notes, verifies checklist, creates GitHub Release
   - Draft + prerelease for non-stable channels
   - No code signing (per requirements)
   - SHA-256 checksums generated for all platforms

2. **Created release notes generator** `scripts/generate_release_notes.py`:
   - Reads CHANGELOG.md for version entry
   - Gets git log summary
   - Generates sections: Summary, Recent Commits, Installers and CLI, Checksums, SBOM and Supply Chain, Licenses, Known Issues, Upgrade Instructions
   - Includes rollback instructions
   - CLI args: `--version`, `--channel`, `--output`

3. **Created verification script** `scripts/check_rc279_github_release.py`:
   - Validates workflow has required jobs, tag trigger, SBOM, release notes, checklist
   - Validates release notes script has all required sections
   - Validates CHANGELOG has versioned entries
   - Checks no code signing
   - Can verify a release directory for required files (RELEASE_NOTES.md, sbom.json, provenance.json, licenses.json, artifacts.json, LICENSE, SHA256SUMS*)

4. **Created test** `backend/tests/test_rc279_github_release.py`:
   - 29 tests across 5 test classes

## Release Artifact Checklist

The release workflow produces:

| Artifact | Source | Purpose |
| --- | --- | --- |
| `*.whl` | build-cli job | Python CLI wheel |
| `*.exe` / `*.msi` | build-desktop (windows) | Windows installer |
| `*.deb` / `*.AppImage` / `*.rpm` | build-desktop (linux) | Linux installer |
| `SHA256SUMS-cli.txt` | build-cli | CLI checksums |
| `SHA256SUMS-desktop-*.txt` | build-desktop | Desktop checksums |
| `sbom.json` | build-sbom | CycloneDX SBOM |
| `provenance.json` | build-sbom | Build provenance |
| `licenses.json` | build-sbom | License report |
| `artifacts.json` | build-sbom | Artifact hashes |
| `RELEASE_NOTES.md` | publish | Generated release notes |
| `LICENSE` / `NOTICE` / `THIRD_PARTY_NOTICES` | publish | License files |

## Verification Results

- `python scripts/check_rc279_github_release.py` → PASS
- `pytest backend/tests/test_rc279_github_release.py -q` → 29 passed

## Limitations

- **Actual GitHub Actions execution**: Requires pushing a `v*` tag to a GitHub repo with Actions enabled
- **Tauri installer packaging**: NSIS/WiX tools may timeout on GitHub runners (same network issue as RC-272)
- **Code signing**: Explicitly excluded per requirements; installers are unsigned
- **Release notes from Issues/PRs**: Current implementation uses CHANGELOG.md + git log; full Issue/PR integration requires GitHub API scripting
