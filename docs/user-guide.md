# User Guide

Rabbit Code has the same local service behind its CLI and web workspace. Use the CLI for repeatable commands and the workspace for route selection, streaming output, version review, and settings.

## CLI workflows

```bash
rabbit analyze "Explain a database migration to a new contributor."
rabbit optimize "Write a release note" --provider offline --template-id general-summary
rabbit templates list --category tech
rabbit templates show tech-code-generation
rabbit history list
rabbit history diff 1 2
rabbit export 2 --format md --output result.md
rabbit evaluate --dataset data/evaluation/prompts.yml --output docs/evaluation-report.md
```

`rabbit prompt` is a compatibility command group for the same analyze, optimize, evaluate, serve, export, templates, and history operations. `rabbit run` and `rabbit tui` use the shared Agent Runtime and support text, JSON, and JSONL output where the command exposes `--output`.

For diagnostics and local data:

```bash
rabbit version
rabbit path --json
rabbit doctor --json
rabbit config show --workspace .
rabbit completion powershell
```

`rabbit uninstall --json` previews application cleanup. Add `--purge-data --yes` only after reviewing the preview.

## GUI workflow

1. Open `/workspace` and select or create the current workspace.
2. Use `/workspace/task` to enter a prompt, choose a template, select a Provider/model, and choose whether prompt history is saved.
3. Run Analyze for deterministic scoring, Stream for incremental model output, or Background for a task that can be monitored and cancelled.
4. Review the optimized prompt and metadata. Accept it into history only after checking the diff.
5. Open `/workspace/review` for a side-by-side change review, `/workspace/models` for local model state, or `/workspace/providers` for Provider discovery and connection tests.
6. Export a selected version from the history panel. `/workspace/diagnostics` shows redacted health information.

The workspace routes currently include:

| Route | Purpose |
| --- | --- |
| `/workspace/home` | Workspace list and entry point |
| `/workspace/task` | Prompt composer and optimization |
| `/workspace/review` | Version/change review |
| `/workspace/terminal` | Terminal process view |
| `/workspace/providers` | Provider and model setup |
| `/workspace/models` | Local model lifecycle |
| `/workspace/assets` | Prompt templates/assets |
| `/workspace/settings` | Workspace-scoped settings |
| `/workspace/diagnostics` | Redacted diagnostics |

## Composer, sessions, and diff

The diamond-star button beside the composer is the prompt optimization action. It captures the current text, cursor, attachment references, and revision before starting. It validates empty or overlong input, changes to a loading state, and lets the same button cancel an in-flight request. A successful result opens the editable optimization diff; the user can replace the selected text, replace all, close the preview, retry, or leave the original draft untouched. A stale revision is not allowed to overwrite a newer draft.

The composer keeps a local revision counter while the request is running. A new edit, route change, or cancellation invalidates stale results. Session-local model selection is stored separately from the workspace default; use the model page to repair a model before selecting it.

The result metadata identifies execution location, Provider, model, selection scope, health, latency, fallback reason, and recovery action. It does not expose a Provider secret. A diff compares the selected version with the active version and shows score delta and changed lines. Deleting a version requires an explicit action and does not silently change another version.

## MCP, plugins, and Hooks

The settings page exposes workspace-scoped MCP and plugin toggles. MCP connections support stdio and streamable HTTP transports, tool discovery, authentication, cancellation, and a write permission gate. Plugins require a manifest, compatible semantic version, allowed source/permissions, an artifact SHA-256, explicit enablement, and an audit record. Hooks run deterministic callbacks around lifecycle and tool events; they are not a replacement for permissions.

Keep these features disabled unless the workspace needs them. Review the minimum permission and data boundary of each server/plugin before enabling it.

## Recovery

- Provider auth/model/region errors: review the Provider setup and use the recovery link; never paste a key into the error report.
- Local model not installed/not ready: open `/workspace/models`, start the runner, verify health, and retry.
- Out of memory: stop another runner/model, lower the model/context size, or use offline rules.
- Timeout or network failure: check diagnostics and retry once; inspect the Provider's retry-after value.
- Stale or cancelled result: re-run from the current composer revision.
