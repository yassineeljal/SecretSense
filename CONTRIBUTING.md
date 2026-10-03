# Contributing

Use Python 3.11 or newer. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e './core[dev,ml,plots,experiments,api]'
pre-commit install
```

Before opening a pull request:

```sh
ruff check core ml api .github/actions-runner
ruff format --check core ml api .github/actions-runner
pytest core/tests ml/tests api/tests --cov=secretsense --cov=ml.scripts --cov=api --cov-report=term-missing --cov-fail-under=85
python -m ml.scripts.build_dataset
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

The exact generated path `ml/data/dataset.csv` is also excluded from Gitleaks;
it contains reproducible invented credential shapes. Keep it Git-ignored. The
generator source, negative review catalog, notebook, and value-free manifest stay
in scope. Never store collected credentials in that excluded path. See the
[dataset guide](ml/README.md) for labels, grouped splits, and reproduction. Clear
notebook outputs before committing and never display individual training values.

All code, documentation, UI text, and commits must be in English. Document
functional changes in the relevant guide and add a dated entry to
`docs/progress.md`, including validation and remaining limitations. Keep commits
focused on one feature. Do not add measured-looking ML metrics without an
evaluation artifact and a reproducible dataset split.

The full test suite requires the optional ML and plotting dependencies. Run the offline baseline
with `python -m ml.scripts.train_baseline` after dataset generation when changing
experiment infrastructure. Do not retune using the existing observed test split;
model-quality changes need a newly reserved holdout. Keep `ml/results/baseline.pkl`
local and Git-ignored. Maintain the aggregate report and model card when recording
a new experiment, including unfavorable results and candidate-population limits.


Sprint 5 development also checks `.github/actions-runner` with Ruff and `action.yml`
through its adapter tests; `actionlint` validates workflows locally when available.
XGBoost experiments need the optional `experiments` extra and macOS `libomp`.
Follow [the fixed experiment protocol](docs/sprint5-experiment.md): do not retune
against either observed holdout. Keep UBJ artifacts local and notebook outputs
cleared. Git-history tests use temporary local synthetic repositories only.

For API and site changes, follow [the local development guide](docs/api-and-web.md).
Run the web lint, format, type, production build, Playwright, and `npm audit --omit=dev` checks.
Keep browser traces and source screenshots disabled; tests assemble synthetic
credentials at runtime. Do not expose local demo servers as a hosted service.

The exact `web/.next/` output tree is excluded from Gitleaks because Next.js
generates signing/encryption keys in build manifests and caches. It is Git-ignored
and must never contain maintained source. Application source, configuration, and
lockfiles remain scanned; do not add real credentials to generated output.

For site/release changes, also validate `npm run build:portfolio` and
`npm run test:portfolio` from `web/`, then rebuild local mode if using the demo.
Keep benchmark values sourced from the existing aggregate reports; never present
synthetic results as real-world accuracy. Run `actionlint` for workflow changes
and `python -m twine check --strict core/dist/*` for release metadata. Keep
`core/LICENSE` identical to the root MIT license. Read [release preparation](docs/release.md)
before configuring a host or registry; build artifacts do not imply publication.
