# Model Licenses

This directory contains license references for local models that Rabbit Code
supports for on-demand download. Models are NOT bundled with Rabbit Code;
users must accept each model's license before download.

## Gemma 3 1B IT

- **License:** LicenseRef-Gemma-Terms (Gemma Terms of Use)
- **URL:** https://ai.google.dev/gemma/terms
- **Status:** Gated — requires user acceptance before download
- **Source:** https://huggingface.co/google/gemma-3-1b-it

## Qwen2.5-Coder 1.5B Instruct

- **License:** Apache-2.0
- **URL:** https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct/blob/main/LICENSE
- **Status:** Open — user must confirm license terms before download
- **Source:** https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct

## Notes

- Model license metadata is maintained in `data/models/manifest.yml`.
- The `LocalInstallCore` (RC-185/RC-191) enforces `license_accepted` before
  any download begins.
- License confirmation version is recorded in the installation state JSON.
