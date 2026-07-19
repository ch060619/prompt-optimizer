# ADR-0015: Gemma Release Selection

- RC ID: RC-190
- Status: Accepted for the controlled manifest; real weight validation remains pending
- Date: 2026-07-19
- Deciders: Rabbit Code engineering

## Decision

The first controlled Gemma entry is `google/gemma-3-1b-it` at the fixed revision recorded in
`data/models/manifest.yml`. Its `gemma-3` chat template and `<end_of_turn>` EOS marker are part of
the manifest contract. The Gemma Terms are gated metadata and must be accepted before download;
the manifest does not grant redistribution rights or bundle weights.

The selected entry is the smallest reviewed Gemma candidate in the current manifest, which keeps
the default local route within the hardware safety recommendation path while leaving larger
variants for a later reviewed entry.

## Consequences

- GUI and CLI use the full source model ID and cannot silently substitute another Gemma family or
  an unreviewed `latest` tag.
- A real runner smoke must verify the fixed family, template and EOS behavior after the model is
  downloaded; the current free test uses the shared in-memory runner contract.
- Gemma license acceptance remains an explicit installation gate.

## Verification

- `backend/tests/test_rc190_gemma_model.py` checks the fixed ID, template, EOS, license gate and
  generation smoke.
- `data/models/manifest.yml` keeps the source revision, file SHA-256 and model-card/license status.
