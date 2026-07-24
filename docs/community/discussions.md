# GitHub Discussions Setup

GitHub Discussions is repository configuration rather than a file-controlled feature. Enable it in the repository settings and create these categories:

| Category | Use |
| --- | --- |
| Announcements | Maintainer release and migration notices |
| Q&A | Usage questions that do not contain secrets or private prompts |
| Ideas | Early proposals before an RC Issue exists |
| Show and tell | User workflows and non-sensitive examples |

Security reports must use the private Security Advisory channel linked by `.github/ISSUE_TEMPLATE/config.yml`. Do not create a public Discussion category for vulnerability reports.

Moderators should link accepted Ideas to an RC Issue with a measurable outcome, test plan, compatibility impact, and provenance statement. Keep roadmap status in `ROADMAP.md` and detailed acceptance evidence in `docs/evidence/RC-xxx/`.
