# Contributing

Use Python 3.11 or newer. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e './core[dev]'
pre-commit install
```

Before opening a pull request:

```sh
ruff check core
ruff format --check core
pytest core/tests --cov=secretsense --cov-report=term-missing --cov-fail-under=85
python -m build core
pip-audit --skip-editable
pre-commit run --all-files
```

The Gitleaks hook scans the working directory at commit time and in CI, including
untracked source files. Its first setup needs network access to obtain its Go
toolchain and dependencies. Activate `.venv` so the Ruff hooks can find Ruff.
Generated Python caches are excluded because they can contain runtime synthetic
test values; source tests remain in scope. Assemble synthetic credential-shaped test
strings at runtime instead of putting complete tokens into fixtures.

All code, documentation, UI text, and commits must be in English. Document
functional changes in the relevant guide and add a dated entry to
`docs/progress.md`, including validation and remaining limitations. Keep commits
focused on one feature. Do not add measured-looking ML metrics without an
evaluation artifact and a reproducible dataset split.
