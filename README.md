# SecretSense

Find potential secrets in local source code without sending it to a remote service.

SecretSense is a Python secret scanner with a working CLI, redacted console and
JSON reports, service-specific patterns, and entropy checks. Local machine
learning, a FastAPI service, and a Next.js demonstration site are planned.

**Status:** foundations and the first rule-based scanner are implemented. There
is no trained model, hosted service, or PyPI release yet. The original project
plan is preserved in English in [the roadmap](docs/roadmap.md).

## Session handoff

Keep this section current after every meaningful change so a new session can
resume without access to previous conversations. Read this README, `AGENTS.md`,
and [the progress log](docs/progress.md) before starting work.

- **Current milestone:** sprints 0 and 1 are implemented: Python packaging, the
  local scanner, CLI, redacted console/JSON reports, tests, and CI configuration.
- **Latest implementation:** commit `2da5536` adds the scanner foundation.
- **Verified locally:** 46 tests pass on Python 3.11, 3.12, and 3.14; coverage on
  3.12 is 97.65%. Ruff, package builds, dependency auditing, and Gitleaks passed.
- **Remote checks:** check the latest [GitHub Actions run](https://github.com/yassineeljal/SecretSense/actions)
  before claiming remote CI success; local checks do not establish that result.
- **Next task:** sprint 2. Add reproducible synthetic-data generation and reviewed
  negative examples under `ml/`, record provenance and template/source groups,
  build at least 5,000 balanced examples, and add an exploration notebook. Keep
  source/template groups separate across training, validation, and test sets.
- **Still planned:** trained ML, calibrated scores, HTML/SARIF, Git-history scanning,
  remediation playbooks, FastAPI, Next.js, deployment, PyPI, and optional Ollama.
- **Standing instructions:** keep all project content in English. Update this
  README and the relevant documentation as work progresses, record actual checks
  and limitations, and never commit real credentials or invent evaluation metrics.

## Quick start

Requires Python 3.11 or newer. Run from this repository's root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e './core[dev]'
secretsense scan ./my-project
```

```sh
secretsense scan ./my-project --format json
secretsense scan ./my-project/.env
```

Exit codes: `0` no candidates, `1` candidates found, `2` invalid input or an
incomplete scan. Reports always mask detected values. Nothing is uploaded and
scanned contents are not written to disk by the scanner.

## What works

- Local UTF-8 file and directory scanning with nested `.gitignore` rules.
- Patterns for 15 services, plus JWTs and private-key headers.
- Entropy checks for literals assigned to secret-like variable names.
- Masked findings with file locations, rule IDs, severity, and explanations.
- Bounded file reads and traversal, with explicit incomplete-scan errors.
- Python library entry points, console output, and versioned JSON reports.
- Unit and CLI tests, Ruff, a Python CI matrix, dependency auditing, and Gitleaks hooks.

The scanner skips symlinks, binary/non-UTF-8 input, oversized files, and common
build/dependency directories. Ignored files can contain secrets: explicitly scan
files such as `.env` when needed. A clean report is not a security guarantee.
See [detection coverage and limitations](docs/detection.md).

## Repository

```text
core/                 Python package, CLI, scanner, reports, and tests
.github/              CI workflow and Dependabot configuration
docs/                 Architecture, roadmap, usage, security, and progress
```

The `ml/`, `api/`, and `web/` applications will be added in their respective sprints.

## Documentation

- [CLI and library usage](docs/cli.md)
- [Detection rules](docs/detection.md)
- [Architecture](docs/architecture.md)
- [Full project roadmap](docs/roadmap.md)
- [Progress and validation log](docs/progress.md)
- [Model card](docs/model-card.md) and [benchmark plan](docs/benchmarks.md)
- [Threat model](docs/threat-model.md) and [security policy](SECURITY.md)
- [Contribution guide](CONTRIBUTING.md)

All code, comments, documentation, and user-facing text are maintained in English.
Every meaningful change must update this README's session handoff; functional
changes must also update the relevant documentation and progress log.

## Development

After the quick-start installation:

```sh
pre-commit install
ruff check core
ruff format --check core
pytest core/tests --cov=secretsense --cov-report=term-missing --cov-fail-under=85
python -m build core
pip-audit --skip-editable
```

Remote CI results are available only after changes are pushed. See the progress
log for checks actually run locally.

Licensed under the [MIT License](LICENSE).
