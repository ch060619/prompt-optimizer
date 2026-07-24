# Security, Privacy, Telemetry, and Data Deletion

This page describes current repository behavior. It does not promise a Provider's retention, training, jurisdiction, or deletion behavior; those terms belong to the selected Provider and account.

## Data boundary

| Data | Default location/behavior | User control |
| --- | --- | --- |
| Prompt history, versions, tasks | Local SQLite under the Rabbit Code data directory | Disable prompt history; delete selected records or all local data |
| Logs and caches | Local application data directories | Retention preview/cleanup and log level |
| Provider credentials | OS-backed SecretStore when available; environment values are process scoped | Remove the credential reference; rotate the upstream key |
| Local models | User-selected model root and checksummed registry | Change root, update/rollback, repair, cleanup, uninstall |
| Telemetry | Off by default; pending events remain local until an explicit product transport exists | Consent toggle and delete pending telemetry |

Cloud requests may include the prompt/messages, selected model, generation parameters, enabled tool definitions/results, request metadata, and a credential in the transport header. The offline rules, Ollama, and LM Studio routes are local, but the local runner and OS may still write their own logs.

## Telemetry event list

When the user opts in, eligible technical fields are versioned by the consent value `rc220-v1`:

- application version and event name;
- duration, result category, and local resource counters;
- selected Provider/model identifier and local/cloud execution location;
- non-secret lifecycle state such as cancellation, fallback, or recovery category.

Prompt text, file contents, workspace paths, credentials, HTTP headers, request bodies, model responses, and raw tool output are excluded. The implementation must keep this list allow-listed; adding a new field requires a code review and privacy review.

## Safe reporting

Use the private GitHub Security Advisory channel described in `SECURITY.md` for undisclosed vulnerabilities. Do not open a public Issue with keys, prompts, personal data, model weights, or exploit details. For ordinary bug reports, use the redacted output from `rabbit doctor --json` and remove workspace paths when they are not needed.

## Deletion and retention

1. Open Settings > Data and run the retention preview.
2. Review log/cache/task/history counts and retained paths.
3. Confirm retention cleanup only after checking the preview.
4. To remove all application data, run the all-local-data preview and explicitly confirm the destructive action. Keep external backup copies only when policy requires them.
5. Remove/rotate Provider keys at the Provider after deleting the local reference; Rabbit Code cannot revoke a key at an external service.

`rabbit uninstall --json` is a dry run. `rabbit uninstall --purge-data --yes --json` explicitly confirms application-data deletion. Model files, external runner caches, shell history, OS backups, and Provider-side records may require separate deletion steps.

## Security limits

- HTTPS is required for cloud endpoints unless the user explicitly configures a local endpoint; local HTTP defaults are bound to loopback.
- A successful connection test is not a license or privacy approval.
- `--json` diagnostics are redacted but should still be reviewed before sharing.
- Code signing, notarization, and malware scanning are release concerns; absence of a signature is not evidence that an artifact is safe.
