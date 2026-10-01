# Model card

Status: **experimental random-forest baseline trained locally on 2026-09-30**.
The CLI defaults to rules and entropy and now supports opt-in model annotations
that retain every candidate. This model is not recommended as a default filter: its held-out synthetic recall is substantially below the scanner baseline.
Scores are uncalibrated and never establish provider-verified credential validity.

## Training and intended use

The baseline supports offline research and sprint 4 integration experiments.
It is not validated for production filtering, real repositories, or credential
validity checks. No network requests, public data collection, or credential
execution are part of training or evaluation. Code and synthetic data use MIT.

The [dataset manifest](../ml/data/manifest.json) describes 6,000 balanced invented
examples across twenty families: 3,600 train, 1,200 validation, and 1,200 test.
Connected source/template groups stay together, holding out entire categories.
Negative review is local template inspection, not independent human adjudication.
The balanced distribution does not reflect real-world prevalence.

The default train and validation splits contain **zero negative scanner candidates**.
Training therefore uses all annotated values, including negatives that the scanner
would never extract. This is an early annotated-value classifier, not a validated
candidate filter. The experiment also evaluates actual scanner spans end to end;
private-key candidates contain just a header, unlike their full annotations.

Thirteen numeric features describe length, entropy, character composition, format
matches, assignment names, placeholders, and environment expressions. Only value
and context enter the feature function. Labels, IDs, categories, provenance, group
and split metadata are excluded. Format and name heuristics can still learn
synthetic-template shortcuts; the model is not independent of regex rules.

Three forest configurations and five thresholds were fixed before test evaluation.
Each forest uses 100 trees, balanced class weights, one worker, and seed 20260930.
Training uses only train rows. Selection maximizes validation F2, then recall,
precision, and closeness to threshold 0.5; the first configuration breaks remaining
ties. There is no train-plus-validation refit. Selected: depth 6, minimum leaf size
2, threshold **0.6**. Annotated validation precision is 96.46%, recall 100%, and
F1 98.20%. These scores are optimistic for candidate filtering because validation
contains no extracted negatives.

## Held-out results and observed failures

See [benchmarks](benchmarks.md) and the machine-readable
[aggregate report](../ml/results/baseline.json) for complete results. On 1,200 test
rows, both annotated-value and candidate-pipeline ML obtain precision 100%, recall
65%, and F1 78.79%; the confusion matrix is `[[600, 0], [210, 390]]` (actual rows,
predicted columns, class order 0/1).

All 300 Stripe shapes are found, but only 90/300 invented database passwords are
retained. All 300 test dummies and 300 documentation URLs are rejected. Rules plus
entropy find 597/600 positives, while flagging all 300 test dummies. Three database
passwords fail the entropy candidate gate; ML misses 207 additional positives.
The learned filter trades away too much recall for the project's objective.

Do not retune on this now-observed test split. Sprint 5 uses new candidate negatives and
a separate fresh holdout, as described below. Further tuning needs another reserved set. Unseen repositories,
independent review, confidence intervals across many groups, calibration, model
drift, and service-format changes remain unevaluated. Family-level metrics with
only one class have undefined positive metrics represented as zero.

## Artifact and reproduction

The local Git-ignored artifact is `ml/results/baseline.pkl`; the versioned report
records its SHA-256:

```text
45b4c1acdcb9e77bee8f6191b8926f7573f40e30c2234f050ae4c40bcfa91084
```

The recorded run uses Python 3.12.13, scikit-learn 1.9.1, NumPy 2.5.3, SciPy 1.18.1,
joblib 1.6.0, and threadpoolctl 3.7.0 on Darwin arm64. The report records the Git HEAD,
dirty working-tree flag, source hashes, feature importances, parameters, timing,
and dataset checksums. The commit alone does not describe this uncommitted run.
See [reproduction instructions](../ml/README.md#baseline-training-and-evaluation).

Loading requires an explicit trusted digest and verifies the same bounded byte
buffer before deserialization. A hash is not a signature: an untrusted pickle and
its accompanying hash must never be accepted. Python/scikit-learn versions must
match the training environment; cross-version pickle compatibility is not
promised. See scikit-learn's [model persistence guidance](https://scikit-learn.org/stable/model_persistence.html).


## Integrated use in sprint 4

Local CLI scoring is explicitly opt-in and retains every rules/entropy finding,
including scores below the frozen 0.6 threshold. It changes neither rule severity
nor candidate exit codes. `above-threshold` means only that the uncalibrated score
meets the artifact threshold; it does not mean a usable or verified credential.
The proposed 0.4/0.8 bands are not implemented pending calibration.

The [integration report](../ml/results/integration.json) reproduces the frozen
baseline on the same observed synthetic test set. All 897 scanner candidates are
retained (390 above threshold, 507 below), preserving 99.5% scanner recall. The
65% recall quoted above applies to hypothetical ML filtering. This reproduction
adds implementation evidence, not a fresh quality estimate. The original artifact
and historical baseline report are unchanged. See [CLI usage](cli.md) for trusted
loading, report fields, failure behavior, and HTML export.

## Sprint 5 evaluation-only XGBoost comparison

A separate [fixed experiment](sprint5-experiment.md) trains a new forest and XGBoost
on 1,200 actual candidate examples with both labels, selects on 600 validation
rows, then evaluates 600 newly generated grouped holdout rows. New authored context
pairs and values are separate from the historical corpus; this is not independent
human review or real-world credential validity. Feature version 1 is unchanged.
Neither the existing trusted forest nor its CLI annotation threshold is replaced.

XGBoost selects 100 trees, depth 3, learning rate 0.1, `hist`, one CPU thread, seed
20261001, and threshold 0.25. The comparison forest selects depth 6, minimum leaf
size 2, and threshold 0.25. Both score 54.55% precision and 100% recall on the fresh
synthetic holdout; XGBoost does not outperform the forest. The remaining 250 false
positives show the ambiguity of provider-shaped offline fixtures. Both reject
50 dummy-prefixed examples. Scores are uncalibrated; the CLI retains all findings.

The Git-ignored native UBJ artifact is for local experiment reproduction only;
CLI loading continues to accept only the independently trusted forest format.
See [aggregate results](../ml/results/xgboost.json), [benchmark interpretation](benchmarks.md),
and [error analysis](../ml/notebooks/04_error_analysis.ipynb). Future feature changes,
calibration, or filtering policies require independent reviewed data and another
reserved holdout: this one has now been observed.
