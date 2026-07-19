# Security Policy

## Supported Versions

Security fixes target the latest `3.x` release and the default branch. Older
versions may receive triage only unless a maintainer explicitly commits to a
backport.

## Private Reporting

Please do not open a public issue for an undisclosed vulnerability. Use the
private [GitHub Security Advisory form](https://github.com/ch060619/prompt-optimizer/security/advisories/new)
for reproduction steps, affected version, impact, and a safe contact method.
Do not attach API keys, prompts, source code, model weights, or personal data.

## Response Targets

Maintainers acknowledge a private report within 2 business days, provide an
initial severity decision within 5 business days, and target a mitigation or
workaround according to this SLA:

| Severity | Target mitigation |
| --- | --- |
| Critical | 72 hours |
| High | 7 calendar days |
| Medium | 30 calendar days |
| Low | Next planned release |

The reporter is credited unless anonymity is requested. Coordinated disclosure
timing is agreed with the reporter and affected dependency maintainers.

## Credential and Key Rotation

Exposed credentials are revoked and rotated immediately. Logs, diagnostics,
telemetry, and issue attachments are reviewed for the same credential before
public disclosure. Never commit secrets; use the OS-backed SecretStore and
redacted diagnostic preview paths.
