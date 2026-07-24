# Contributing to Rabbit Code

Start with [the contribution guide](docs/contribution.md). Every change should name its RC requirement, state the smallest observable outcome, and record the verification command and result.

Before opening a pull request:

```bash
python scripts/check_docs.py --run
python scripts/workspace.py verify
```

The PR template requires tests, compatibility impact, sources/provenance, and license/NOTICE review. Do not include API keys, private prompts, model weights, screenshots with secrets, or undisclosed security details. Use the private Security Advisory form for vulnerabilities.
