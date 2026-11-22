# JD Lens

A Chrome side panel extension plus a local helper that scores job descriptions against the user's own resume data. See README.md and docs/GETTING-STARTED.md.

## Rules
- Never commit personal data: `master/master-resume.md`, `applications/`, `tailored/`, `stories/`, `answers/`, built `data/*.json`. They are git-ignored; keep it that way.
- Tests use the sample master (`master/master-resume.template.md`) and the fictional fixtures in `tools/tests/fixtures/`. Do not put real names, employers or paths in code, mocks, fixtures or docs.
- Run only the tests for what you changed while iterating (`tools/tests/render_panel.py --only=...`); the full suite is for before a release.
- No em dashes in any file. Commit only when asked.
