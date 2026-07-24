# RC-270 Evidence

<!-- RC ID: RC-270 -->

## Scope

Added bug and feature Issue Forms, repository Issue configuration with a private Security Advisory contact link, PR traceability/verification/compatibility/provenance fields, English and Chinese contribution entry points, Code of Conduct, Roadmap, Discussions setup, and Keep a Changelog file.

## Verification

- `python -m pytest backend/tests/test_rc270_governance.py -q`: 3 passed.
- `python scripts/check_docs.py --run`: passed.
- YAML forms require RC ID and measurable/reproducible verification fields; blank Issues are disabled; undisclosed security reports route to `/security/advisories/new`.

## Limits

GitHub Discussions categories and repository settings must still be enabled by a repository maintainer; the committed setup document does not pretend to change remote GitHub configuration.
