# Repository working agreements

- Write code, comments, documentation, commit messages, and user-facing text in English.
- Document every functional change in the relevant guide and `docs/progress.md`.
- Follow `docs/roadmap.md`; distinguish delivered features from planned work.
- Keep scanning local. Never execute scanned content or validate detected credentials remotely.
- Never include complete detected values or source snippets in reports, logs, or exceptions.
- Use synthetic credentials assembled at runtime in tests; never commit real credentials.
- Run Ruff, relevant pytest checks, the package build, and dependency auditing for Python changes.
- Before starting the web application, inspect its applicable instructions and the installed
  Next.js documentation at `node_modules/next/dist/docs/` if that directory is available.
- Do not claim model metrics, remote CI success, deployment, or publication without evidence.
