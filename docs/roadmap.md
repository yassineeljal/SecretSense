# Project roadmap

This is the English version of the original project brief. It describes the full
intended product; check [the progress log](progress.md) for delivered work.
SecretSense remains the working project name.

## Product and shared architecture

Three interfaces share the Python core:

```text
Python core: scan → candidates → feature extraction → local ML → score → report
    ├── CLI: secretsense scan ./my-project
    └── FastAPI service
            └── Next.js site: demo, documentation, model results
```

The CLI is the primary tool. The API powers the demonstration site. Planned inputs
are local directories, public repository URLs, and pasted text.

The final pipeline will:

1. Accept input and enumerate files, excluding binaries and dependency directories.
2. Extract candidate secrets with regular expressions and entropy.
3. Convert candidate values and context into numeric features.
4. Apply a local model to estimate whether a candidate is a real secret.
5. Classify scores above 0.8 as likely secrets, 0.4–0.8 as uncertain, and below
   0.4 as ignored. These are proposed thresholds pending calibration; "confirmed"
   must never imply provider-verified validity.
6. Optionally use local Ollama assistance for uncertain cases, with redacted input.
7. Attach service-specific remediation guidance.
8. Produce console, JSON, HTML, or SARIF output.

## Target repository layout

```text
README.md, LICENSE, SECURITY.md, CONTRIBUTING.md
.github/workflows/ci.yml, release.yml
core/
  pyproject.toml
  secretsense/
    cli.py
    scanner/          walker, Git history, patterns, entropy, engine
    features/         candidate/context feature extraction
    model/            train, predict, evaluate, trusted artifacts
    report/           console, JSON, HTML, SARIF
    remediation/      service playbooks
    llm/              optional Ollama integration
  tests/
ml/
  data/               raw, generated, dataset.csv
  scripts/            generate_fake_secrets, collect_false_positives, build_dataset
  notebooks/          exploration, features, model comparison, error analysis
api/
  main.py, schemas.py, limits.py, routes/scan.py
web/                  Next.js application
docs/
  architecture.md, model-card.md, threat-model.md, benchmarks.md
```

Create implementation directories as their work begins; do not ship empty modules
as completed features. Model artifacts will need a recorded trusted checksum.

## Technology choices

| Layer | Planned technology | Purpose |
| --- | --- | --- |
| Core | Python 3.11+ | Shared scanning and ML ecosystem |
| CLI | Typer | Typed arguments and generated help |
| Ignore patterns | pathspec | Git-style ignore semantics |
| ML | scikit-learn, then evaluate XGBoost | Lightweight local inference |
| Data work | pandas | Dataset preparation and analysis |
| API | FastAPI and Pydantic | Validated HTTP interface |
| Site | Next.js, TypeScript, Tailwind | Demo and documentation |
| Tests | pytest and Playwright | Core, API, and browser validation |
| CI | GitHub Actions | Lint, tests, builds, audits |
| Deployment | Vercel and Render or Fly.io | Candidate web/API hosts; verify plans at deployment |

Before writing the site, read any applicable `AGENTS.md` and installed Next.js
instructions in `node_modules/next/dist/docs/` when available. No existing Next.js
application or installed framework documentation was present at project start.

## Website

| Route | Content |
| --- | --- |
| `/` | One-sentence pitch, animated demo, Try button, verified badges, installation |
| `/scan` | Paste code or upload a file, analyze, inspect results |
| `/results` | Findings, scores, risk, explanations, remediation, severity filters |
| `/how-it-works` | Pipeline diagram and accessible model explanation |
| `/benchmarks` | Regex versus ML, precision/recall, confusion matrix |
| `/docs` | Installation, CLI, report formats, GitHub Actions integration |
| `/model` | Model card, training data, limitations, biases, failure cases |
| `/security` | Privacy policy and threat model |
| `/about` | Author information and supplied GitHub/LinkedIn links |

Planned components: `CodeInput`, `ScanButton`, `FindingCard`, `RiskBadge`,
`ConfusionMatrix`, `MetricsChart`, `PipelineDiagram`, and `CopyCommand`.
Show only masked values, never complete detected secrets. Metrics must come from
real evaluation runs. Personal biography and profile links need verified input.

## API

| Method and route | Planned behavior |
| --- | --- |
| `POST /api/scan` | Accept `{ "content": "...", "filename": "..." }`; return findings |
| `POST /api/scan/repo` | Scan a size-limited public repository URL |
| `GET /api/health` | Health status |
| `GET /api/model/info` | Model version, measured metrics, training date |

Process pasted content in memory without persistence or content logging. Enforce
request size (initial target: 1 MiB), rate limits, deadlines, and concurrency
limits. Handle repository fetching, malicious files, oversized trees, and archives
with explicit limits before enabling those inputs. Never execute scanned content.
Redact values before optional LLM use. Accept only trusted model artifacts and
verify checksums before loading formats such as pickle that can execute code.
Use Dependabot, `pip-audit`, and Gitleaks for the project's own security.

## Dataset and evaluation

Target 5,000–20,000 balanced examples:

| Source | Examples | Label |
| --- | --- | --- |
| Synthetic generators | AWS, GitHub, Stripe, Slack, JWTs, private-key shapes | 1 |
| Invented configuration | Random database passwords and similar literals | 1 |
| Documentation | your_key_here, API_KEY placeholders, changeme | 0 |
| Public tests | Reviewed dummy values | 0 |
| Environment reads | os.getenv and process.env references | 0 |
| Benign identifiers | Hashes, UUIDs, build IDs | 0 |

Record provenance and licensing; do not collect usable credentials. Public test
values need review because a test file can also contain a real leak. Split by
source repository and generated template family to prevent leakage across
training, validation, and test sets.

Prioritize recall and report precision, recall, F1, and a confusion matrix.
Compare regex alone, rules plus entropy, the local model, and model plus optional
LLM. Analyze missed and false-positive cases, and test on unseen repositories.
Use four notebooks for exploration, feature work, model comparison, and errors.

## Delivery sprints

A sprint is a suggested week of work, not an automatic commitment to elapsed time.
Sprints 0–6 are implemented; sprint 7 informational pages and release preparation
are implemented locally. Public hosting and PyPI publication remain pending. Sprint 2's reproducible
CSV is generated locally and Git-ignored; its generators, negative review catalog,
manifest, and exploration notebook are maintained in `ml/`. Review here means
local template inspection, not independent human adjudication. See the
[dataset guide](../ml/README.md) and [validation log](progress.md). Sprint 3 adds
an offline forest, trusted artifact checksum, feature/comparison notebooks, and
measured synthetic results. Its recall regression rules out default filtering;
sprint 4 therefore implements opt-in annotations that retain every finding.
Trusted artifact checks, JSON score semantics, HTML reports, frozen-model scanner
reproduction, and PNG/SVG comparison figures are delivered. The proposed 0.4/0.8
bands remain planned pending calibration; the artifact threshold (0.6 for this
baseline) controls annotations only. Sprint 5 delivers service playbooks, bounded local Git-history scans, SARIF 2.1.0,
a reusable Action, an error-analysis notebook, and a separate XGBoost experiment
with new candidate negatives and fresh grouped holdout evaluation. XGBoost offers
no advantage over the retrained forest on that synthetic holdout. Both holdouts
are now observed; future tuning needs another reserved set. Remote Action smoke execution is verified in sprint 7 CI; independent human
adjudication and unseen-repository evaluation remain unverified.

| Sprint | Work | Deliverable |
| --- | --- | --- |
| 0: foundations (2–3 days) | MIT license, README, packaging, structure, lint/tests CI, Gitleaks hooks | Installable foundation with validated checks |
| 1: classic scanner | Ignore-aware traversal, 15 services, entropy, CLI, unit tests | Functional scanner without AI |
| 2: dataset | Fake-secret generator, negative examples, labels, cleaning, exploration notebook | At least 5,000 examples in dataset.csv |
| 3: first model | Features, random forest, initial evaluation, model-comparison notebook | Model artifact and measured results |
| 4: integration | Prediction pipeline, thresholds, console/JSON/HTML, artifact checksums, benchmark | Local ML-enabled CLI and comparison figures |
| 5: remediation | Service playbooks, Git-history scan, error analysis, XGBoost evaluation, SARIF, reusable Action | CI-ready scanner with remediation |
| 6: API and site | Bounded FastAPI service, home/scan/results pages, masking, API and browser tests | Working local demonstration |
| 7: polish and release | Benchmark/how-it-works/model/security pages, hosting, PyPI release, final README/GIF/badges, policy docs | Public, deployed, installable product |
| 8: optional LLM | Redacted Ollama requests for uncertain cases, --llm option, measured benefit | Documented advanced mode (implemented; measured benefit pending) |

Console and JSON reporting were brought forward to sprint 1 so the first scanner
is usable and its masking contract can be tested. Early security, contribution,
model-card, and benchmark documents establish limits before those features ship.

Sprint 6 delivers bounded in-memory text scanning, health/engine information,
fully redacted API reports, and local home/scan/results pages with API and browser
tests. Repository URLs, archives, hosted scanning, and API model loading remain planned.
Sprint 7 supplies the six informational pages, interactive recorded benchmarks,
privacy policy, portfolio hosting configuration, and a guarded manual release
workflow. Hosting accounts and registry ownership are not established, so the
sprint 7 public/deployed/published deliverable is not yet complete. See [the API/site guide](api-and-web.md).

## Definition of done

- Implemented behavior is tested and relevant checks pass.
- Remote CI is green once a branch is pushed; local checks alone are not remote CI.
- README or relevant documentation is updated in English.
- Features have focused commits when changes are committed.
- A short written progress entry records what works, validation, and remaining work.

The final portfolio should demonstrate trained and evaluated ML, reproducible
benchmarks, a candid model card, threat modeling and security controls, CI and
packaging discipline, and an actually deployed usable product.
