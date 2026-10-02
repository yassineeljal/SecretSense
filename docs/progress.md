# Progress log

Every functional change must update this log and the relevant usage or design
documentation. Every meaningful change must also update the README session
handoff. Record actual validation separately from planned checks.

## 2026-10-01 — Sprint 7: informational site and release preparation

### Delivered

- Added how-it-works, benchmarks, documentation, model, security/privacy, and about
  pages with page titles, shared navigation, responsive layouts, accessible controls,
  and copyable public setup commands with failure feedback.
- Added an interactive benchmark explorer that imports the recorded baseline and
  XGBoost aggregate JSON directly at build time. Experiment and method selection
  update precision/recall/F1 bars and labeled confusion matrices. Synthetic limits,
  population differences, unfavorable historical recall, finding retention, and
  source links remain explicit. No model training or evaluation was rerun.
- Added a portfolio build mode: home links to local setup, `/scan` has no input or
  upload, and CSP excludes the loopback API. The existing local demo is preserved.
  Vercel configuration selects portfolio mode; no API hosting is configured.
- Added privacy policy, changelog, hosting/release guide, README static/GIF previews
  from redacted/aggregate pages, and a live GitHub CI badge. About uses only the
  repository identity; no author biography or LinkedIn information is invented.
- Added manual release preparation with build-only default, wheel/sdist checks,
  fresh-environment smoke test, artifact retention, and separate OIDC publishing.
  Publishing requires an enabling variable, exact version tag, successful push CI
  for the commit, and separately configured registry ownership/protected environments.
  Added package project URLs and bundled the MIT license.
- Pushed prior sprint 2–6 work as `9e78ab0`. Its first remote CI run passed browser,
  hooks, Action smoke, and all Python test steps, but the Python 3.11 audit failed
  on runner-bundled setuptools 79.0.1 (PYSEC-2026-3447; fix 83.0.0). Updated CI to
  upgrade packaging tools before installation and disabled matrix fail-fast so
  independent results finish. No vulnerability exclusion was added.
- Updated the root/core/web READMEs, architecture, API/site, benchmarks, roadmap,
  threat model, security, contribution, and release documentation.

### Validation

- 147 Python/API tests pass with 92.79% coverage at the delivery checkpoint.
- 18 Chromium local-site checks pass across desktop/mobile emulation, including
  existing live scans plus all guide routes, responsive layouts, every exposed
  benchmark method versus the JSON evidence, matrix orientation, and clipboard
  success/failure. Two additional portfolio checks pass without an API process.
- Local and portfolio production Next.js builds, TypeScript, ESLint, Prettier,
  npm audit (zero vulnerabilities), Ruff, Python isolated sdist/wheel build,
  Twine strict metadata checks, pip-audit, and actionlint pass. The built wheel
  installs and scans in a fresh environment outside the checkout; it includes the
  MIT license and excludes datasets/model artifacts.
- Visually inspected desktop and mobile benchmark pages. README captures contain
  only the illustrative redacted home panel, pipeline, and aggregate metrics.
- Implementation `5a9024d` is pushed to `origin/main`.
  [Remote CI](https://github.com/yassineeljal/SecretSense/actions/runs/36950882794)
  passes all seven jobs: Python 3.11–3.14, hooks, Action smoke, and Node 24 web.
  This verifies the runner setuptools upgrade and both browser build modes on Linux.
- The [build-only release rehearsal](https://github.com/yassineeljal/SecretSense/actions/runs/36950893726)
  passed, including fresh wheel installation, and retained `python-distributions`;
  its publication job was skipped. No hosted deployment or registry publication
  has been attempted. Existing Starlette and ESLint tooling caveats remain as
  recorded in sprint 6. Pre-commit secret scanning, Markdown targets, and Git
  whitespace checks pass.
- Restored the local-mode build and loopback review servers on ports 3000 and 8000.

### Handoff

Sprint 7's site, policy, and release preparation are implemented. Its roadmap
promise of a public, deployed, published product is **not complete**. No host/PyPI
project was supplied, so hosting/release preparation is complete but launch remains
pending. Remote CI and build-only release rehearsal are now verified. Required next
steps are owner-selected host/project configuration, privacy contact/log review,
and verified deployment/publication. The public API remains deferred pending authentication and shared
controls; use portfolio mode for a documentation-only host. Independent evaluation,
calibration, and optional Ollama remain future work.

## 2026-10-01 — Sprint 2–6 delivery checkpoint

- Revalidated the accumulated sprint 2–6 implementation before committing and pushing
  at the user's request: 147 pytest checks pass with 92.79% coverage; Ruff,
  isolated Python sdist/wheel build, pip-audit, web lint/format/build/typecheck,
  npm audit, all 12 existing desktop/mobile browser checks, and all pre-commit hooks pass.
- Sprint 7 follows this checkpoint. Remote CI, deployment, and package publication
  are separate steps; their outcomes will be recorded when established.

## 2026-10-01 — Sprint 6: bounded local API and browser demonstration

### Delivered

- Added FastAPI health, engine information, and text scan endpoints sharing the
  core rules/entropy engine. Strict Pydantic inputs and generic errors never echo
  source, filenames, detected values, or exception details.
- Defined limits before enabling web input: 1 MiB streamed request bodies, two
  simultaneous POSTs including uploads, 30 POSTs per rolling minute, a ten-second
  request deadline, five-second worker deadline, 1,000 findings, and 2 MiB output.
  Limits reject excessive work without reporting a partial scan as complete.
- Added disposable subprocess scanning over pipes, worker termination/reaping on
  timeout or cancellation (including cancellation during startup), and generic
  failure handling before ASGI logging. No source execution, content persistence,
  repository fetching, model upload, or provider validation is supported.
- Fully redacted API values and replaced submitted filenames with `submitted.txt`.
  Kept all candidates and remediation, with no API model scores or new metrics.
- Added Next.js 16.3.8/React 19.3/TypeScript/Tailwind home, scan, and results pages:
  illustrative animated preview, local CLI instructions, paste/UTF-8 file input,
  loading/errors, finding severity filters, explanations, and expandable remediation.
- Kept scan input out of Next.js and browser storage. Requests go directly to the
  loopback API. Input clears on submission; redacted results live only in React
  memory and clear on reload/site exit or explicit clearing. Added keyboard labels,
  status messages, responsive layouts, reduced motion, local-only assets, and CSP.
- Added API tests and Playwright desktop/mobile Chromium coverage; extended Python
  CI and configured a Node 24 browser/build/audit job, npm Dependabot, and a lockfile.
  Excluded tests from coverage measurement and generated web output from Git.
- Added [the API/site guide](api-and-web.md), API/web READMEs, and updated root/core
  README, architecture, threat model, contribution guide, roadmap, and handoff.

### Validation

| Check | Local result |
| --- | --- |
| Full pytest on Python 3.12.13 | 147 passed; 92.79% combined core/ML/API statement coverage, excluding test code |
| API boundaries | 19 tests cover masking, strict input, chunked sizes, slow uploads, concurrency/rate/host/origin checks, caps, generic failures, no execution, and worker cleanup |
| Browser tests | 12 passed against production Next.js and real local API; Chromium desktop and mobile emulation |
| Browser contracts | Real scans, redaction, input clearing, refresh reset, memory-only state, text/binary/oversized files, filters/remediation, busy/errors/recovery, no external requests, responsive/reduced-motion behavior |
| Visual inspection | Home and scan at desktop width, results at mobile width; no browser page errors during the manual flow |
| Ruff | Lint and formatting passed across core, ML, API, and Action adapter |
| Web tooling | ESLint with zero warnings, Prettier check, TypeScript, and production Next.js build passed |
| Package | Python sdist/wheel build passed; API extra installed successfully from the checkout |
| Dependency audits | pip-audit: no known vulnerabilities (editable scanner skipped); npm audit: zero vulnerabilities |
| Workflow and docs | actionlint, local Markdown targets, and Git whitespace passed |
| Gitleaks/pre-commit | Passed after excluding only generated Next.js output; Ruff hooks also passed |

An initial browser run needed selectors scoped to `main` because Next.js adds its
own alert announcer, and an explicit navigation wait before reload. The corrected
suite passes. The first Gitleaks run flagged six generated Next.js manifest/cache
keys under the Git-ignored `web/.next/` tree. Only that generated tree is now
excluded; application source remains scanned. The final Gitleaks and Ruff hooks pass.

The isolated Python package build passed before the environment changed to
restricted network access. A later rebuild could not resolve PyPI; the final
sdist/wheel was rebuilt successfully offline with `--no-isolation`, using cached
Hatchling/trove-classifiers/tomlkit extracted to temporary storage. The application's
installed dependency set was unchanged. Local preview servers were left running
on loopback ports 3000 and 8000 for review.

ESLint 10 was incompatible with the installed Next.js React lint plugin; the site
pins ESLint 9.39.5, which npm marks deprecated. Its lint/audit checks pass; revisit
this tooling pin when the plugin supports ESLint 10. API tests pass with one
Starlette warning about the future migration from httpx to httpx2. Neither warning
is hidden. Tests ran on macOS with Node 26.5.0 and Python 3.12.13; Node 24/Linux and
other Python versions are CI configuration, not locally verified in this sprint.

### Handoff

Sprint 6 is implemented locally. Existing sprint 2–5 edits are preserved. No
commit, push, deployment, publication, or remote CI success is claimed. The demo
is unauthenticated and loopback-only; rate limits are per process and startup uses
one worker. Bounds are not an OS sandbox or secure memory erasure. Browser traces,
video, and source screenshots remain disabled. Repository URL input and archives
are not enabled. The optional core model and all historical evaluation artifacts
remain unchanged.

Next is sprint 7: evidence-backed informational pages, hosting/release preparation,
policy docs, and final portfolio polish. Public hosting first needs authentication,
TLS/ingress/logging review, and a shared limit strategy. Independent evaluation,
calibration, unseen repositories, release/publication, and optional Ollama remain
planned; do not retune against the two observed holdouts.

## 2026-10-01 — Sprint 5: history, remediation, SARIF, Action, and XGBoost

### Delivered

- Added static playbooks for all 15 services, JWTs, private keys, and generic
  entropy candidates. JSON 1.2, console, HTML, and SARIF expose response guidance.
  No revocation, remote verification, edits, or history rewriting is performed.
- Added `scan_history` / `--history` with local ref resolution, raw object reads,
  path/blob deduplication, snapshot commit/blob provenance, and explicit commit,
  entry, per-blob, total-byte, Git-output, and deadline limits. Shallow/missing/
  oversized/truncated history produces incomplete reports and exit 2.
- Disabled inherited Git configuration, global/system config, hooks, filters,
  lazy fetch, and transport protocols. No checkout or scanned source execution.
  Symlinks/submodules are skipped. Historical tracked files ignore current excludes.
- Added SARIF 2.1.0 with encoded locations, rule remediation, model/history metadata,
  metadata-only fingerprints, and incomplete-scan notifications. No source snippets,
  full values, or source-line/secret hashes enter SARIF.
- Added a Linux composite Action that installs its own package in an isolated
  environment, treats inputs as data, writes SARIF in runner temporary storage,
  normalizes paths to the workspace, and always fails incomplete scans. Upload is
  caller-controlled. A remote Action smoke job is configured, not claimed successful.
- Added a fixed-protocol 2,400-row synthetic experiment with new paired context
  groups and candidate negatives in all splits. Both forest and XGBoost select
  solely on validation; holdout generation occurs after both choices are frozen.
  The default run verifies value disjointness against the historical 6,000 rows.
- Added aggregate experiment/provenance results, evaluation-only local UBJ artifact,
  a fourth error-analysis notebook, environment pins, and documentation. XGBoost
  remains optional and does not change CLI loading or default finding retention.

### Measured fresh-holdout results

On 600 new synthetic examples (300 per label):

| Method | Precision | Recall | F1 | TN / FP / FN / TP |
| --- | ---: | ---: | ---: | --- |
| Regex only | 50.00% | 66.67% | 57.14% | 100 / 200 / 100 / 200 |
| Rules plus entropy | 50.00% | 100.00% | 66.67% | 0 / 300 / 0 / 300 |
| New forest filter | 54.55% | 100.00% | 70.59% | 50 / 250 / 0 / 300 |
| XGBoost filter | 54.55% | 100.00% | 70.59% | 50 / 250 / 0 / 300 |

XGBoost does not improve on the new forest. Both reject 50 dummy-prefixed examples;
250 authored fixture candidates remain. Provider-shaped fixtures can share the
features of intended positives. These are synthetic intent labels, not validity
or real-world quality. The historical baseline and 0.6 CLI annotation threshold
are preserved. Both holdouts are now observed and must not become tuning data.

### Validation

| Check | Local result |
| --- | --- |
| Full pytest on Python 3.12.13 | 128 passed; 92.30% combined core/tooling statement coverage |
| Ruff lint and formatting | Passed for 50 Python/notebook files, including the Action adapter |
| History contracts | Deleted/ignored paths, snapshot deduplication, bare/shallow repositories, non-UTF-8 paths, resource caps, timeouts, safe errors, and inference fallback passed |
| Git execution/network isolation | Filters/symlinks and hostile promisor/transport configuration tests passed without executing their marker commands |
| SARIF | Clean, candidate, and incomplete-history reports validated against the SARIF 2.1.0 JSON schema; privacy/location contracts passed |
| Action | `actionlint` passed; adapter inputs, failure policy, workspace paths, isolated-wheel execution, and repository self-scan passed locally |
| Fresh experiment reproduction | Exact dataset hash, selections, all metrics, and UBJ bytes match; current source/protocol digests verified |
| Historical baseline | Original trusted pickle and aggregate report unchanged; scanner reproduction agrees with historical metrics |
| Error-analysis notebook | Code cells executed with aggregate-only output; all four notebooks have cleared outputs |
| Package and isolated wheel | sdist/wheel built; isolated import/SARIF/Action smoke passed; no CSV/pickle/UBJ bundled or optional ML imported by basic scanning |
| Dependency audit | `pip-audit --skip-editable`: no known vulnerabilities; local editable scanner skipped |
| Gitleaks/pre-commit | Passed across tracked and new source files |
| Documentation and whitespace | Local Markdown targets and `git diff --check` passed |

An initial added non-UTF-8 path test hit macOS filesystem restrictions; the final
test builds the byte-named Git tree directly and passes without requiring such a
working-tree filename. The final suite has no skipped tests. Model reproduction
is verified only in this recorded local environment, not across platforms.

Local validation installed XGBoost and JSON Schema tooling in `.venv`, plus
Homebrew `libomp` for XGBoost and `actionlint` (with ShellCheck) for workflow checks.
macOS OpenMP requirements and the experiment environment are documented.

### Handoff

Existing sprint 2–4 work is preserved. No commit, push, publication, deployment,
or remote CI success is claimed. Sprint 5 is complete locally. Next is sprint 6:
bounded API and local demonstration site. Independent adjudication,
real-repository evaluation, score calibration, release, and Ollama remain planned.

## 2026-09-30 — Sprint 4: optional local scoring and HTML reports

### Delivered

- Integrated opt-in local prediction into `scan_text`, `scan_path`, and the CLI
  using `--model` plus `--model-sha256`. Rules and entropy remain the default;
  ordinary scanning imports neither scikit-learn nor Matplotlib.
- Preserved every finding, rule severity, and candidate exit code regardless of
  model score. Artifact-selected threshold annotations are `above-threshold`
  (score >= threshold) or `below-threshold`; scores are explicitly uncalibrated.
  The roadmap's proposed 0.4/0.8 confidence bands remain deferred pending calibration.
- Added bounded 256-candidate prediction batches, numeric output validation, and
  correct occurrence-specific context for repeated values. Prediction failures
  preserve that file's unscored findings, record a generic error, and produce an
  incomplete report with exit 2. The in-memory primitive raises `PredictionError`.
- Hardened trusted loading: regular-file/nonblocking access, symlink refusal where
  supported, exact-byte size/checksum checks before unpickling, feature/fitted
  forest/class/threshold validation, and value-free dependency/deserialization
  errors. An untrusted pickle plus its supplied hash remains unsafe.
- Added JSON schema 1.1 model provenance, threshold, score kind, retention policy,
  and per-finding score/decision fields. Console/HTML show rounded scores while
  decisions and JSON use the original numeric score. Rules/unscored fields are null.
- Added self-contained HTML with escaped dynamic text, accessible table markup,
  completeness/errors, score explanations, restrictive CSP, and no scripts or
  remote assets. Reports contain no complete values or source snippets.
- Added frozen-model integration reproduction and aggregate-only Matplotlib PNG/SVG
  exports, with separate optional plotting dependencies and CI installation.
  Updated CLI, detection, architecture, threat model, model card, benchmark and
  dataset guides, roadmap, package README, contribution guide, and session handoff.

### Measured integration results

The unchanged sprint 3 model and its frozen 0.6 threshold reproduce the historical
metrics through the scanner on the same 1,200 observed synthetic test rows:

| Policy | Candidates retained | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Default rules / CLI ML annotations | 897 | 66.56% | 99.50% | 79.76% |
| Hypothetical above-threshold filtering | 390 | 100.00% | 65.00% | 78.79% |

The CLI retains all 507 below-threshold candidates. These are not assumed false
positives: the historical filter misses 207 additional positive examples beyond
candidate extraction's three misses. No baseline retraining, threshold tuning,
or fresh model-quality claim was made. The original `baseline.json` and pickle
are unchanged. [integration.json](../ml/results/integration.json) records current
source hashes, dataset/artifact/baseline checksums, environment, metrics, counts,
and single-run comparison timing. The [figures](benchmarks.md#sprint-4-integration-reproduction-and-figures)
show measured synthetic results and distinguish retained findings from filtering.

### Validation

| Check | Local result |
| --- | --- |
| Full pytest on Python 3.12.13 | 97 passed; 91.84% combined core/tooling statement coverage |
| Ruff lint and formatting | Passed for all 40 Python/notebook files |
| Frozen integration reproduction | Exact agreement with recorded default and hypothetical-filter metrics |
| Provenance and artifact integrity | Current integration source hashes match; original artifact and baseline report checksums unchanged |
| Privacy and inference failures | Threshold boundaries, batching, occurrence context, unscored preservation, and safe errors tested |
| Artifact trust | Checksums, schemas, missing dependencies, special files, and symlink refusal tested |
| HTML and report contracts | Escaping, CSP, clean/incomplete output, all three formats, masking, and exit codes tested |
| Figure exports | Two comparisons in SVG and PNG; PNGs visually checked; aggregate-only export tested |
| Package build and wheel smoke | sdist/wheel built; isolated wheel import/render passed; no CSV or pickle bundled |
| Optional dependency isolation | Rules scanning works with ML imports blocked; wheel scanning imports neither ML nor plotting packages |
| Dependency auditing | `pip-audit --skip-editable`: no known vulnerabilities; local editable package skipped |
| Gitleaks/pre-commit | Passed across tracked and new files |

### Remaining work and handoff

Sprint 4 is implemented locally. Pre-existing sprint 2–3 changes were preserved.
This session has not committed, pushed, deployed, or published; remote CI success
is not claimed. Final documentation links and Git whitespace are checked locally.

Next is sprint 5: service-specific remediation playbooks, bounded Git-history
scanning, error analysis, XGBoost evaluation, SARIF, and a reusable GitHub Action.
New model-quality work requires independent candidate negatives and a fresh
reserved holdout; the observed test split must not become tuning data. Calibration,
API/site work, release, and optional Ollama remain planned. Continue retaining all
findings unless a later independently evaluated policy justifies a change.

## 2026-09-30 — Sprint 3: offline random-forest baseline

### Delivered

- Added a versioned 13-number value/context feature interface; labels, IDs,
  provenance, categories, source/template groups, and splits cannot enter it.
  Features describe lengths, entropy, composition, formats, and assignment context.
- Extracted shared scanner candidates as offsets without retained values. Existing
  rules, entropy policy, finding redaction, locations, and CLI behavior are preserved.
  The same offsets now drive offline candidate-pipeline evaluation.
- Assessed candidate coverage: train extracts 1,800/1,800 positives and 0/1,800
  negatives; validation extracts 600/600 positives and 0/600 negatives; test
  extracts 597/600 positives and 300/600 negatives. Candidate-only binary training
  is therefore unsuitable for this corpus. The baseline trains on annotated values
  and reports that population mismatch explicitly.
- Added optional `ml` dependencies, deterministic 100-tree forests, three fixed
  parameter configurations, and five thresholds. Selection uses validation F2,
  recall, precision, then closeness to 0.5; no test input reaches selection and no
  train/validation refit occurs. Selected depth 6, leaf size 2, threshold 0.6.
- Created the Git-ignored local artifact `ml/results/baseline.pkl` and versioned
  aggregate [report](../ml/results/baseline.json), recording provenance/checksums,
  environment, source hashes, dirty Git state, parameter trials, feature importances,
  candidate coverage, per-family metrics, confusion matrices, and timing.
- Added a trusted artifact loader: explicit independently trusted SHA-256, bounded
  reads, verification of the exact bytes before unpickling, and schema validation.
  A matching hash is not proof of trust; arbitrary external pickles remain unsafe.
- Added training-feature and model-comparison notebooks, a pinned reproduction
  environment, tests for experiment isolation/privacy/reproduction, and CI ML
  dependencies. Updated guides, model card, benchmarks, roadmap, and README handoff.

### Measured results

On the reserved 1,200-row synthetic test set:

| Method | Precision | Recall | F1 | TN / FP / FN / TP |
| --- | ---: | ---: | ---: | --- |
| Regex only | 100.00% | 50.00% | 66.67% | 600 / 0 / 300 / 300 |
| Rules plus entropy | 66.56% | 99.50% | 79.76% | 300 / 300 / 3 / 597 |
| Annotated-value model | 100.00% | 65.00% | 78.79% | 600 / 0 / 210 / 390 |
| Actual candidate pipeline with ML | 100.00% | 65.00% | 78.79% | 600 / 0 / 210 / 390 |

ML retains all 300 Stripe shapes and only 90/300 database passwords. It rejects
all 300 test dummies and 300 documentation URLs. Of the 210 missed passwords,
three already fail candidate extraction; 207 more are rejected by ML. Validation
has no extracted negatives and cannot validate this recall/precision tradeoff.
This is a measured unfavorable baseline, not justification for default ML filtering.
No parameters or features were changed in response to test results.

Artifact SHA-256:
`45b4c1acdcb9e77bee8f6191b8926f7573f40e30c2234f050ae4c40bcfa91084`.
The unchanged synthetic CSV checksum remains
`d30ffc5475edbfd9e410613e3ed66c0711c5cf44d7ed102585dae642d5a44c10`;
its manifest now includes the training script in source provenance.

### Validation

| Check | Local result |
| --- | --- |
| Full pytest on Python 3.12.13 | 67 passed; 93.35% combined core/tooling statement coverage |
| Final baseline/notebook checks | 5 passed after notebook formatting updates |
| Full 6,000-row reproduction | Identical model bytes, selected model/threshold, and all evaluation metrics |
| Artifact integrity | Source/manifest digests match the recorded run; validation predictions survive save/load |
| Privacy and trust tests | Value-free reports/candidate representations/errors; bad hashes and oversized artifacts rejected before deserialization |
| Ruff lint and formatting | Passed, including all three notebooks |
| Source distribution and wheel | Built successfully; wheel contains neither model pickle nor dataset CSV |
| `pip-audit --skip-editable` | No known vulnerabilities; editable scanner package skipped |
| Gitleaks and pre-commit | Passed across tracked and new source files |

Model reproduction was verified on the same Python 3.12.13/Darwin arm64 environment;
there is no cross-version model claim. Timestamps and wall-clock timing differ on
reruns. The dataset's earlier cross-version checks remain recorded below. Synthetic
labels express authored intent, not usable or provider-verified credentials.

### Remaining work and handoff

Sprint 3 is implemented locally. Existing Sprint 2 changes were preserved; this
session has not committed, pushed, deployed, or published anything. Remote CI is
not established by these local checks. The CLI remains rules plus entropy.

Next is sprint 4: opt-in prediction integration with trusted loading, score/report
semantics, HTML reports, and benchmark figures. Preserve the rules default given
the measured recall regression. Improving model quality requires independent hard
candidate negatives and a fresh reserved holdout; the observed test set must not
become tuning data. Calibration, unseen repositories, independent adjudication,
XGBoost, SARIF/remediation/history, API/site, releases, and Ollama remain planned.

## 2026-09-30 — Sprint 2: reproducible synthetic dataset

### Delivered

- Added standard-library-only generators for ten positive credential-shape
  families and ten negative families. All content is invented locally; no public
  repositories, real credentials, or remotely verified values are used.
- Added a negative-template review catalog with provenance, MIT licensing,
  rationale, and ambiguity notes. Review is local code/template inspection, not
  independent human adjudication of every row. Public-test collection is deferred.
- Built `ml/data/dataset.csv`: 6,000 unique examples, 3,000 per label, with 3,600
  training, 1,200 validation, and 1,200 test rows. Every split is balanced.
  The CSV stays local and Git-ignored; rerunning the builder reproduces it.
- Recorded the seed, generator version, source/CSV checksums, group membership,
  counts, provenance, and limitations in the value-free `ml/data/manifest.json`.
  CSV SHA-256: `d30ffc5475edbfd9e410613e3ed66c0711c5cf44d7ed102585dae642d5a44c10`.
- Added normalization, exact text/value deduplication, conflict rejection, and
  schema/balance checks. Connected source/template groups, including transitive
  links, remain in one split. Entire families are held out; split categories differ.
- Added an exploration notebook that verifies the artifact and reports only
  aggregate counts, family coverage, lengths, entropy, and a length histogram.
  Its code cells execute in tests; no notebook server or new dependency is needed.
- Extended CI, Ruff configuration, and pytest discovery to cover `ml/`. Excluded
  only the exact generated CSV path from Gitleaks; generator source, review
  catalog, manifest, and notebook remain scanned. A manifest checksum initially
  triggered a generic-key rule because it followed a secret-related filename;
  separating path and checksum fields fixed that without another exclusion.
- Updated the dataset guide, architecture, model card, benchmark plan,
  contribution instructions, roadmap, and README handoff.

### Validation

| Check | Local result |
| --- | --- |
| pytest on Python 3.12.13 | 57 passed; 94.02% combined core and dataset-tooling statement coverage |
| Default generation | 6,000 rows; zero duplicates; both labels balanced in every split |
| Reproducibility | Matching CSV and manifest across Python 3.11.16, 3.12.13, and 3.14.7 |
| Notebook execution | All Python code cells executed successfully; output contains no example values |
| Ruff lint and formatting, including notebook | Passed |
| Source distribution and wheel build | Passed |
| `pip-audit --skip-editable` | No known vulnerabilities; local editable scanner package skipped |
| Gitleaks working-directory scan | No findings with the generated CSV excluded |
| Pre-commit on tracked and new source files | Gitleaks, Ruff lint, and Ruff formatting passed |
| Documentation links, cleared notebook outputs, Git whitespace | Passed |

Tests cover reproducibility, seed variation, balance and uniqueness, transitive
group isolation, order independence, insufficient independent groups, conflicting
duplicates, normalization, corrupted CSVs, invalid counts, CLI behavior, provenance
checksums, safe object representations, and value-free notebook/CLI output.
Cross-version checks here verify generation, not the full test suite on those
additional interpreters. Python 3.13 remains configured for CI, not tested locally.

### Remaining work

Sprint 2 is implemented locally; this session has not committed or pushed changes,
and no remote CI, deployment, publication, or model metrics are claimed. Synthetic
labels express authored intent, not credential validity. Twenty generator families
and a balanced synthetic distribution are insufficient evidence of real-world
performance. Independently reviewed hard negatives and unseen repository data
remain future evaluation work.

Next is sprint 3: assess candidate-extraction coverage, add features without label
or provenance leakage, train a local random-forest baseline, tune on validation,
evaluate with the reserved test split, and produce the model-comparison notebook,
measured results, and a trusted artifact checksum. ML integration, richer reports,
remediation, Git-history scanning, API/site work, release, and Ollama remain planned.

## 2026-09-30 — Persistent session handoff

- Added the current milestone, verified checks, implementation commit, remaining
  scope, and concrete sprint 2 starting point to the README.
- Made README maintenance and reading repository context at session start explicit
  in `AGENTS.md`, so future sessions can resume without conversation history.
- The user authorized pushing the local scanner foundation and this documentation
  update to `origin/main`. The initial delivery entry below records its state at
  the time of implementation; consult Git and GitHub Actions for current remote state.
- Documentation-only change; validate local links, Git whitespace, and commit hooks.

## 2026-09-30 — Foundations and first working scanner

### Delivered

- Created the Python package, Typer CLI, and importable `scan_text`/`scan_path` API.
- Added 15 service patterns, JWT and private-key-header detection, and entropy
  checks for literals assigned to secret-like names.
- Implemented nested `.gitignore` handling, built-in directory exclusions,
  bounded reads/traversal, symlink and special-file skipping, and incomplete-scan
  reporting. Bounded assignment-name matching avoids excessive regex work on
  repeated word boundaries.
- Added masked console and schema-versioned JSON reports, stable locations,
  explanations, and explicit exit codes. These two report formats were moved
  forward from sprint 4 to make the baseline usable and test its masking contract.
- Added MIT licensing, contribution/security policies, working agreements,
  architecture, usage, detection coverage, model-card and benchmark plans, and
  a threat model. Preserved the original project brief as an English roadmap.
- Configured GitHub Actions for Python 3.11–3.14, Ruff, pytest/coverage, builds,
  dependency auditing, Gitleaks, and Dependabot. Installed the local commit hook.
- Configured Gitleaks to scan the working directory, including untracked source.
  Its upstream hook otherwise scans only staged changes, which is insufficient
  in a fresh CI checkout. Excluded generated Python caches after runtime synthetic
  test tokens were correctly detected in bytecode and pytest node IDs; source
  test files remain covered.

### Validation

| Check | Local result |
| --- | --- |
| pytest on Python 3.11.16 | 46 passed |
| pytest on Python 3.12.13 | 46 passed; 97.65% statement coverage |
| pytest on Python 3.14.7 | 46 passed |
| Ruff lint and formatting | Passed |
| Source distribution and wheel build | Passed |
| `pip-audit --skip-editable` | No known vulnerabilities in installed dependencies; local editable package skipped |
| Gitleaks working-directory scan | No findings after generated-cache exclusions |
| Pre-commit across all tracked files | Gitleaks, Ruff lint, and Ruff formatting passed |
| Local documentation links and Git whitespace checks | Passed |
| CLI self-scan and `python -m secretsense` | Successful, no candidates in package source |

Regression coverage includes every detection rule, redaction in reports and object
representations, locations, duplicate suppression, placeholders, ignore anchoring
and negation, nested traversal limits, invalid/oversized ignore configuration,
binary/encoding/size exclusions, symlinks, named pipes, I/O errors, terminal filename
escaping, a long-input subprocess deadline, and CLI exit codes.

### Remaining work

Foundations and the classic scanner are implemented and validated locally. Remote
CI has not run on this change; Python 3.13 is configured in CI but was not tested
locally. This delivery remains local and has not been pushed, deployed, or published.

Next is sprint 2: reproducible synthetic data generation, reviewed negative
examples, provenance/grouped splits, at least 5,000 examples, and an exploration
notebook. ML inference, calibrated scores, HTML/SARIF, Git-history scanning,
remediation playbooks, API/site work, publication, and Ollama remain planned.
No model accuracy or benchmark result is claimed.
