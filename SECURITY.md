# Security Policy

## Reporting a Vulnerability

**Do NOT open a public issue for security vulnerabilities.**

Use GitHub Security Advisories to report vulnerabilities privately:

1. Go to the repository's Security tab.
2. Click "New security advisory".
3. Provide a clear description, steps to reproduce, and potential impact.

We acknowledge reports within 72 hours.

## Response Timeline

| Severity | Acknowledgment | Fix Release |
| --- | --- | --- |
| Critical | 24 hours | 7 days |
| High | 48 hours | 14 days |
| Medium | 72 hours | 30 days |
| Low | 1 week | Next release |

## Scope

This policy covers:

- Rabbit Code CLI (`pip install rabbit-code`)
- Rabbit Code Desktop (Tauri installers)
- Rabbit Code API (FastAPI backend)
- Rabbit Code frontend (React/Vite)

## Out of Scope

- Third-party provider APIs (OpenAI, Anthropic, Google, etc.) — report to the respective provider.
- Local model vulnerabilities — report to the model publisher (Google, Qwen team).
- Operating system vulnerabilities — report to the OS vendor.

## Security Best Practices for Users

- Store API keys in environment variables or system keychain, not in plain text.
- Use `rabbit config show` to verify no sensitive values are exposed.
- Keep Rabbit Code updated to the latest stable release.
- Run `rabbit doctor` to diagnose installation issues.
