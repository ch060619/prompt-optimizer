# ADR-0014: Local Runner Strategy

- RC ID: RC-187
- Status: Accepted for the adapter boundary; real process integration remains pending
- Date: 2026-07-19
- Deciders: Rabbit Code engineering

## Decision

Ollama is the default local runner. llama.cpp is the supported alternative behind the same
`LocalRunnerAdapter` lifecycle contract: pull, load, generate, stream, stop, list, remove and
health. The Agent Core and optimization service receive this contract and do not issue
runner-specific commands.

Both candidates are recorded as MIT sources in the existing local-model license manifest. Ollama
has the lower first-run integration cost because its managed runtime and local HTTP API reduce
binary lifecycle work. llama.cpp remains the alternative for users who need a user-managed binary,
different GPU build options or a direct `llama-server`/CLI deployment.

## Consequences

- The default and alternative can be tested with the same in-memory adapter contract without a
  network request or installed model weight.
- Real Ollama HTTP and llama.cpp process adapters must be added behind this boundary after the
  model manifest, health, resource, and installation policies are ready.
- The GUI and CLI select a runner by stable ID; they do not depend on Ollama-specific commands.

## Verification

- `backend/tests/test_rc187_runners.py` exercises the full lifecycle for both runner IDs.
- `docs/research/local-model-license-manifest.yml` fixes the MIT source and revision metadata for
  both candidates; no runner binary or model weight is bundled.
