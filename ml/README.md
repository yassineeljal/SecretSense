# Synthetic dataset tooling

Sprint 2 delivers a locally generated dataset and an aggregate-only exploration
notebook. Sprint 3 adds the offline baseline, and sprint 4 adds integrated scoring
verification and exported benchmark figures described below. No real credentials
or public repository data are collected. Dataset generators are development
utilities outside the installed package and require only Python 3.11+ and its
standard library; training uses the optional ML dependencies.

From the repository root, using the development environment:

```sh
python -m ml.scripts.build_dataset
pytest core/tests ml/tests
```

The default command creates **6,000 examples**, evenly divided between labels,
in `ml/data/dataset.csv`. It also writes `ml/data/manifest.json`, containing the
seed, generator version, source and CSV SHA-256 checksums, counts, split membership,
provenance, license, and limitations. The manifest is versioned; the CSV is a
reproducible local artifact and is ignored by Git. The generator replaces these
two outputs when rerun. No timestamps or machine paths enter the artifacts.

```sh
python -m ml.scripts.build_dataset --seed 20260930 --per-family 300
python -m ml.scripts.build_dataset --seed 42 --per-family 250 --output-dir /tmp/secretsense-data
```

There are twenty families, with 1–1,000 examples per family allowed. Use at least
250 per family for the sprint's 5,000-example minimum. Smaller runs are supported
for development. The default 300 yields 3,600 training, 1,200 validation, and 1,200
test examples, each balanced. Reproducibility means the same code, seed, and count
produce byte-identical CSV and manifest files. Source changes alter the manifest
checksums even when they do not change the CSV. The tool prints counts and a
checksum only; it does not print generated values or contexts.

## Generators and label review

`scripts/generate_fake_secrets.py` invents ten positive families: AWS, GitHub,
GitLab, Stripe, Slack, JWTs, private-key shapes, database passwords, Google API
keys, and SendGrid. Label **1** means an invented credential shape, not an issued,
usable, or provider-verified credential. JWT signatures are random bytes. Private
key bodies are deliberately invalid and contain no cryptographic key. Nothing
is sent to a provider or executed.

`scripts/collect_false_positives.py` creates ten negative families: documentation
placeholders, environment expressions, UUIDs, content hashes, build identifiers,
documentation URLs, test dummies, versions, CSS palettes, and numeric identifiers.
Label **0** applies to their deliberately benign authored contexts. The filename
describes the intended training role; it does not assert that the scanner flags
every negative. Labels are independent of scanner output.

The review catalog, [negative_templates.json](data/negative_templates.json), records
the rationale and ambiguity for each negative family. Review means local inspection
of the generators and template semantics during this implementation, not independent
human adjudication of every row. A test filename, dummy marker, UUID, or hash-like
shape alone cannot establish a negative label in real source code. No external
test fixtures were imported, so there is no external source license to infer.
All templates and generated examples use this repository's MIT license.

## Data contract and cleaning

| Column | Meaning |
| --- | --- |
| `sample_id` | SHA-256 of the normalized example text |
| `text`, `value` | Invented context and candidate material; local training data only |
| `label` | 1 credential shape; 0 benign authored context |
| `category`, `template_family` | Generator category and indivisible template family |
| `source_group`, `source_id` | Split isolation group and versioned generator provenance |
| `provenance`, `license`, `review_status` | Origin, permissions, and review method |
| `split` | `train`, `validation`, or `test` |

The builder normalizes line endings and surrounding whitespace, rejects missing
values and invalid labels, and removes exact text/value duplicates inside a group.
Duplicate material with conflicting labels or groups causes a value-free error.
The final CSV is sorted by content-derived ID and checked for uniqueness, class
balance, and group isolation. Quoted CSV fields preserve multiline key shapes.

Template families and source groups form connected components. Any families
linked through a common source, including transitive links, stay in one split.
Components are ordered deterministically with a seeded hash, then assigned toward
60/20/20 per-label targets. Whole groups take priority over exact split ratios;
the builder fails if a split cannot contain both labels. The current equal-size
families meet the targets exactly. Different seeds change both generated material
and group assignments; choose and record a seed before evaluation, not by selecting
the best test score.

All current rows are generated, so a source group denotes a synthetic generator
family, not an external repository. Future imported examples must use repository
identity as their source group. The connected-component splitter supports that
grouping, but remote collection and external-data review are not implemented.
Shared formatting wrappers are not separate families. Entire credential and
negative categories are held out, so coverage varies by split. This is an early
generalization test with only twenty independent families, not evidence of
real-world accuracy. Exact deduplication is not semantic deduplication.

## Exploration and safe handling

Open [01_exploration.ipynb](notebooks/01_exploration.ipynb) in an optional Jupyter
installation using the development Python kernel. Run all cells after building
the dataset. The notebook verifies the CSV checksum and row/group contracts,
then shows label counts, family coverage, length/entropy summaries, and a length
histogram. Tests execute its Python cells without needing a notebook server.
It can run from the repository or notebook directory. `SECRETSENSE_DATA_DIR`
can point to a different generated output directory.

Keep notebook outputs cleared before committing. Never display individual values
or context snippets in notebooks, reports, exceptions, or logs. These generated
training artifacts are separate from scanner reports, whose redaction contract
is unchanged. Only the exact default CSV path is excluded from Gitleaks; generators,
review catalog, manifest, and notebook remain scanned. Custom output locations
inside the repository remain subject to secret scanning. Do not use the CSV
exclusion for collected data or actual credentials.

Only candidate text/value and features derived from them may become model inputs.
Exclude label, ID, category, provenance, source/template groups, review status,
and split metadata from features. The baseline below assesses candidate extraction
coverage and uses validation-only selection before held-out evaluation. Harder
independently reviewed negatives
and unseen real repositories remain necessary before real-world quality claims.

## Baseline training and evaluation

Sprint 3 adds an optional scikit-learn environment, reusable numeric features,
validation-selected random forests, trusted local model artifacts, and two more
notebooks. Dataset generation itself remains standard-library-only.

```sh
python -m pip install -e './core[dev,ml]'
python -m ml.scripts.build_dataset
python -m ml.scripts.train_baseline
```

The trainer reads and verifies the local CSV, trains on the train split, selects
parameters and a threshold on validation only, freezes the artifact, and then
evaluates test. It overwrites `ml/results/baseline.pkl` (Git-ignored) and
`ml/results/baseline.json` (versioned aggregate report). Custom `--data-dir` and
`--output-dir` directories are supported. Reports contain counts and metrics only,
never individual values or source snippets. This command is for the authored
synthetic dataset, not arbitrary untrusted input or collected credentials.

The default scanner extracts no negatives from train or validation, so candidate-only
binary training cannot work with this split. The baseline trains on **all annotated
values** and reports both annotated-value quality and actual candidate-pipeline
quality, plus regex and rules-plus-entropy baselines. Candidate-pipeline evaluation
uses scanner offsets; private-key headers are shorter than their annotations.
The scanner's candidate offsets retain no raw values. Optional CLI annotations
use these same spans without changing finding retention. Candidate coverage is
measured separately for each label and split.

`core/secretsense/features/` exposes a versioned, fixed 13-number feature vector:
length, entropy, uniqueness, lower/upper/digit/symbol ratios, hexadecimal shape,
newlines, format match, secret-like assignment prefix, placeholder marker, and
environment reference. The interface accepts only value and context. Features
must not receive provenance, grouping, labels, IDs, or split metadata. This excludes
explicit metadata leakage but does not eliminate synthetic-template shortcuts.

The forest uses 100 trees, balanced classes, one worker, and seed 20260930. Depth
and minimum leaf configurations are `(6, 2)`, `(12, 2)`, and `(unlimited, 1)`;
thresholds are 0.25, 0.4, 0.5, 0.6, and 0.75. Selection maximizes validation F2,
then recall, precision, and closeness to 0.5; the first configuration wins ties.
The chosen model is not refitted on validation. Scores are **uncalibrated**.
Do not optimize features, thresholds, or hyperparameters against observed test
results; future quality improvements need a fresh independent holdout.

The recorded model misses many held-out database passwords. Read the
[model card](../docs/model-card.md) and [benchmark interpretation](../docs/benchmarks.md)
before using it. Sprint 4 adds opt-in CLI inference that retains all candidates;
the current model is not recommended as a default filter.

For exact environment reproduction of the recorded run, use Python 3.12.13 and:

```sh
python -m pip install -r ml/requirements-baseline.txt
```

The report records dependency versions, feature schema, source hashes, Git HEAD
and dirty-state flag, dataset/manifest checksums, selection trials, family metrics,
feature importances, runtime environment, and timing. Same-environment reruns must
agree on quality results and artifact bytes; timestamps and wall-clock timings
will differ. Different dependency versions may change the fitted artifact. No
cross-platform or cross-version artifact reproducibility is claimed.

Only load a pickle produced by a trusted local run, with a digest from trusted
metadata, using `load_trusted_artifact(path, expected_sha256=...)`. The loader
checks a 32 MiB limit and the SHA-256 of the exact bytes before unpickling, then
checks the feature schema. A matching attacker-supplied checksum does not make a
pickle safe. Artifacts are not bundled in the wheel or downloaded automatically.

- [02_features.ipynb](notebooks/02_features.ipynb) summarizes training features only.
- [03_model_comparison.ipynb](notebooks/03_model_comparison.ipynb) reads the aggregate
  report and displays selection, coverage, precision/recall/F1, and family confusion
  matrices. It never retrains or unpickles a model.

Both support `SECRETSENSE_DATA_DIR`; comparison also supports
`SECRETSENSE_RESULTS_DIR`. Tests execute all code cells. Keep outputs cleared.

## Integration benchmark and figures

Use the existing frozen sprint 3 artifact and dataset, or reproduce them in their
recorded environment first. Do not retrain merely to export figures.

```sh
python -m pip install -e './core[dev,ml,plots]'
python -m ml.scripts.benchmark_pipeline \
  --model-sha256 45b4c1acdcb9e77bee8f6191b8926f7573f40e30c2234f050ae4c40bcfa91084
python -m ml.scripts.plot_benchmarks
```

Only provide a digest from independently trusted training metadata. The benchmark
loads the trusted artifact through the installed predictor, scores test rows through
`scan_text`, checks that every finding is retained, and verifies that retained and
above-threshold-only metrics exactly match the frozen baseline. It never trains,
selects thresholds, or updates the historical `baseline.json`/`baseline.pkl`.
It writes aggregate results to `ml/results/integration.json`, including checksums,
source/environment provenance, candidate counts, and single-run timing. That timing
includes rules/scored comparisons and is not a latency benchmark. Options include
`--data-dir`, `--baseline`, `--model`, `--model-sha256`, and `--output`.

The plot exporter requires the optional `plots` extra (Matplotlib), reads only
`baseline.json`, and writes `quality-comparison` and `confusion-matrices` in SVG
and PNG to `ml/results/figures/`. Use `--report` and `--output-dir` for custom paths.
Both tools replace their named outputs on rerun. No individual values or source
snippets enter the reports or figures. Model training dependencies and plotting
dependencies remain optional for ordinary CLI scanning.

## Sprint 5: fresh candidate experiment and error analysis

The [fixed protocol](../docs/sprint5-experiment.md) introduces 2,400 independently
authored synthetic examples in twelve paired positive/negative context groups:
1,200 train, 600 validation, 600 test. Each group stays in exactly one split.
Both labels produce actual candidates in every split, fixing the earlier corpus's
missing training/validation candidate negatives. Fixtures have deliberate benign
intent, but token shape alone cannot distinguish them from intended positives.
Labels and review express local authorship, not independent human adjudication or
provider validity. All new templates are MIT-licensed project code. No source
repositories are downloaded and nothing is remotely validated.

```sh
python -m pip install -e './core[dev,experiments]'
# On macOS, install the OpenMP runtime first: brew install libomp
python -m ml.scripts.evaluate_xgboost
```

XGBoost's [installation guide](https://xgboost.readthedocs.io/en/stable/install.html)
explains platform dependencies. For the recorded environment, use
`ml/requirements-experiments.txt` with Python 3.12.13. Rules-only users do not need
XGBoost, OpenMP, or scikit-learn.

The command requires the historical local CSV/manifest by default to verify exact
value disjointness (`--historical-data` changes that directory). New rows are
reproduced in memory; their canonical JSON checksum, groups, label coverage,
protocol checksum, source hashes, versions, selections, and metrics are recorded
in [results/xgboost.json](results/xgboost.json). Raw new rows are not written to a
report or CSV. It writes an evaluation-only native `xgboost.ubj` artifact locally,
checks its validation predictions after reload, and records its hash. That artifact
is ignored by Git and cannot be loaded through the CLI's forest-only predictor.
`--output-dir` selects a separate report/artifact directory; reruns replace these
named outputs. The historical forest and its reports remain unchanged.

Both models train on actual scanner spans, using unchanged feature version 1.
Selections use validation only; the test rows are first constructed after both
models and thresholds are frozen. The selected forest uses depth 6/leaf size 2;
XGBoost uses depth 3, 100 estimators, learning rate 0.1, CPU histograms, and one
thread. Both selected threshold 0.25. This is a synthetic experiment, not a CLI
threshold update or calibrated probability model.

Both hypothetical filters reached 54.55% precision / 100% recall on 600 holdout
examples, versus 50% / 100% for rules plus entropy. See the
[benchmarks](../docs/benchmarks.md) for confusion matrices and limitations.
[04_error_analysis.ipynb](notebooks/04_error_analysis.ipynb) reads aggregate reports,
shows historical/fresh errors by group, and never loads source rows or a model.
It supports `SECRETSENSE_RESULTS_DIR`. Keep notebook outputs cleared. The holdout
is now observed and cannot be reused to tune a future model.
