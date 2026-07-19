# Rabbit Code Threat Model

RC IDs: RC-211

## Data Flow

1. A user enters prompts, workspace paths, provider references, or local-model actions in the GUI/CLI.
2. The desktop surface sends versioned protocol requests to the loopback App Server.
3. The Agent Core reads approved workspace context, calls a selected local or remote provider, and emits redacted events.
4. Tools and extensions run behind capability approval, path/environment validation, and the platform sandbox boundary.
5. Secrets remain in the OS-backed SecretStore. Optional telemetry and diagnostic exports are disabled until explicit user consent.

Trust boundaries are the GUI/CLI to App Server boundary, App Server to workspace and SecretStore, Agent Core to tools/extensions, and local process to remote Provider. Remote Provider requests are opt-in per configured route and never receive local content by default.

## STRIDE

| ID | Threat | Control | Verification |
| --- | --- | --- | --- |
| T1 | Spoofing a local App Server client | Loopback bind, per-start token, strict Host/Origin/protocol | RC-207 negative request tests |
| T2 | Tampering with plugins, models, or updates | Locked manifests, HTTPS provenance, SHA-256 verification, atomic install | RC-208/RC-209 negative tests |
| T3 | Repudiation of dangerous tool actions | Frozen approval snapshots and structured audit events | RC-202/RC-203 tests |
| T4 | Information disclosure through secrets, prompts, or diagnostics | SecretStore references, sensitive-file policy, public-output redaction, preview-gated diagnostics | RC-179/RC-180/RC-206/RC-210 tests |
| T5 | Denial of service through tools, providers, or local models | Capability policy, bounded process/model concurrency, budgets, cancellation, retry limits | RC-196/RC-198/RC-204 tests |
| T6 | Elevation of privilege by commands or extensions | argv-only execution, environment allowlist, sandbox capability report, extension permission allowlist | RC-204/RC-205/RC-208 tests |

## Security Gates

CI runs Ruff and strict type checks as SAST-adjacent static gates, the repository secret scanner, dependency audits (`pip-audit` and production `npm audit`), deterministic CycloneDX SBOM drift checks, and Dockerfile checks. High-confidence findings block the build. The scan is intentionally conservative about test fixtures: product paths are scanned, while negative-test fixtures are reviewed by their dedicated tests.

## Assumptions and Residual Risk

The App Server is a local desktop component, not a public service. A compromised operating-system account is outside this model. Real external vulnerability databases, container image CVEs, and platform-specific sandbox enforcement remain environment-dependent and are reported by CI/release scans rather than fabricated locally.
