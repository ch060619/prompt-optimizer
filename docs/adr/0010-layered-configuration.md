# ADR-0010：分层配置与敏感字段来源

- RC ID: RC-065
- Status: Accepted for the current local CLI and service boundary
- Date: 2026-07-17
- Deciders: Rabbit Code engineering

## Decision

Configuration is resolved in this strict order, with each later layer overriding only fields it
provides:

```text
default < user < workspace < session < cli
```

The locations and lifetimes are:

| Layer | Location | Lifetime |
| --- | --- | --- |
| default | typed registry in `ConfigService` | application code |
| user | `<app-data>/config.json` | user profile |
| workspace | `<workspace>/.rabbit-code/config.json` | workspace |
| session | `ConfigService.resolve(session=...)` | current session memory |
| cli | `ConfigService.resolve(cli=...)` / `rabbit config show --override` | one command |

Each registered field declares its value type, sensitivity, scope, nullable behavior, allowed
layers, and optional minimum. Unknown fields, invalid types, out-of-scope overrides, and invalid
numeric limits fail before a merged snapshot is returned.

## Current Fields

`provider`, `model`, and `base_url` are provider-scoped runtime values. `timeout_seconds`,
`max_retries`, and `rate_limit_per_minute` are runtime values. `api_key` is a nullable,
user-secret-scoped field and may only be supplied by the user layer. Existing environment-variable
compatibility remains owned by the Provider registry until a later migration explicitly adopts the
layered resolver for outbound requests.

The runtime snapshot retains the actual secret for the authorized process, but `ConfigSnapshot.display`
and `rabbit config show` return only `secret://config/api_key` or `<not configured>`. No CLI table,
source query, or error message includes the secret value. OS keychain storage remains a later
desktop/security task.

## Consequences

The same merge and validation rules can be used by CLI, GUI, and App Server callers, while session
and CLI overrides remain non-persistent. The current implementation provides the service and CLI
surface; wiring every Provider consumer to this resolver is intentionally a separate migration so
the existing environment compatibility contract remains stable.
