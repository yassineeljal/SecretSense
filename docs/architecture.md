# Architecture

SecretSense is a monorepo with one Python engine shared by a CLI, a
FastAPI service, and a Next.js demonstration site.

```text
Local files → bounded walker → regex / entropy candidates
                                 ├─ default: redact findings
                                 └─ opt-in: features → trusted local ML → annotate + redact
                                                     ↓
                                          console / JSON / HTML / SARIF

Browser → bounded loopback API → disposable scanner → redacted JSON
Planned: deployment, optional local LLM
```

The current implementation lives in `core/secretsense/`: `scanner/walker.py`
handles input scope, `scanner/patterns.py` defines rules, `scanner/entropy.py`
calculates entropy, and `scanner/engine.py` creates findings. `report/` serializes
those findings and `cli.py` handles arguments and exit codes. `scan_text` and
`scan_path` are the library entry points. Raw values are transient and never stored
in a finding; there are no source snippets, credential checks, or network calls.

`pathspec.GitIgnoreSpec` provides pattern semantics; the walker applies each
directory's rules relative to that directory. See its
[API documentation](https://python-path-specification.readthedocs.io/en/latest/api.html).
The CLI uses [Typer command groups](https://typer.tiangolo.com/tutorial/commands/callback/).
CI uses a Python matrix following the
[GitHub Actions Python guide](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).

`ml/scripts/` now implements local synthetic-data generation and dataset
construction, separate from the installed scanner. It produces a Git-ignored
6,000-row CSV and a versioned value-free provenance/checksum manifest. Connected
source/template groups are assigned to train/validation/test splits. The notebooks
explore aggregate data/features and compare measured models.
`features/` provides a versioned numeric interface; `model/` implements offline
random-forest selection, trusted checksum-verified loading, and optional prediction.
The optional `ml` extra supplies scikit-learn; basic scanning does not import it.
`scanner/candidates.py` supplies shared offsets without retaining raw values, so
offline pipeline evaluation uses the same candidate boundaries as reports.
Training uses annotated values because candidate-only train/validation lack
negatives. Aggregate results are versioned in `ml/results/`; the pickle stays local. See the
[dataset guide](../ml/README.md) for the data contract and limitations.

Sprint 4 adds `model/predict.py`: explicit trusted loading, numeric batches of up
to 256 candidates, and uncalibrated score annotations. Every candidate is retained;
rule severity and exit codes remain unchanged. Inference errors preserve unscored
findings and mark the report incomplete. JSON schema 1.1 carries model provenance,
threshold, scores, and decisions. `report/html_report.py` produces escaped,
self-contained HTML with no scripts or remote assets. Neither basic scanning nor
HTML reporting imports scikit-learn or Matplotlib.

The integrated benchmark checks the frozen artifact against historical sprint 3
metrics. A separate Matplotlib exporter reads aggregates only and produces PNG/SVG
figures. Sprint 5 adds static `remediation/` playbooks and an error-analysis notebook.
A future stage may add `llm/`. CLI defaults remain rules plus entropy.
`api/` and `web/` share the scanner with request limits described in
[the API/site guide](api-and-web.md). See [the roadmap](roadmap.md).


Sprint 5 adds `scanner/history.py` and `scan_history`: bounded local Git subprocesses
read raw tree/blob objects without checking out source. Unique path/blob snapshots
feed the same candidate/prediction/redaction engine. Commit/blob IDs identify the
observed snapshot. JSON 1.2 includes remediation and history provenance;
`report/sarif.py` emits metadata-only SARIF 2.1.0. The root composite Action installs
its own scanner and writes a local temporary report; it does not upload results.

`ml/scripts/evaluate_xgboost.py` independently generates new paired context groups,
trains forest/XGBoost on actual candidates, freezes validation-only choices before
the fresh holdout, and writes aggregate results and a local evaluation-only UBJ
artifact. XGBoost is an optional `experiments` dependency, not a CLI predictor.
No model replaces the default rules pipeline. See the [experiment protocol](sprint5-experiment.md).


Sprint 6 adds `api/main.py`, Pydantic input schemas, a streaming ASGI admission
boundary, and a disposable subprocess worker that imports the shared `scan_text`
engine. Source travels over stdin; worker stdout contains fully redacted reports.
Deadline/cancellation kills and reaps the child. The service has no repository
fetcher, model loader, content persistence, or source execution path.

The Next.js App Router site renders `/`, `/scan`, and `/results`. A browser-side
form calls only the loopback API; source does not traverse Next.js. A React context
holds redacted results in memory across internal navigation, never in browser
storage. Tailwind/global CSS provide responsive layouts and reduced motion.
No external assets, analytics, or API keys are required. Both servers bind to
loopback; authentication and deployment remain sprint 7 design work.

## Informational site and release boundary

Sprint 7 adds server-rendered guide pages plus a client benchmark explorer receiving
only selected aggregate metrics from versioned JSON. There is no server-side scan
route in Next.js. Local mode renders the existing client scanner; the portfolio
build renders installation guidance at `/scan` and excludes loopback API connections
from its CSP. Mode changes require a rebuild. The Vercel configuration builds only
the portfolio. The core wheel now includes MIT licensing and project metadata.
A separate manual release workflow defaults to validated build artifacts; gated
publication requires independently configured registry ownership and environments.
See [release preparation](release.md) for operational boundaries.
