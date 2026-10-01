# Sprint 5 experiment protocol

This protocol is fixed before running the fresh holdout evaluation. Do not tune
features, parameters, thresholds, or data in response to holdout outcomes.

Use independently authored synthetic context groups with both intended credential
shapes and benign fixture candidates. No baseline CSV rows enter this experiment.
Entire paired context/format groups belong to one split. Train groups: GitHub,
AWS, database password, npm, Slack, and generic session token. Validation groups:
GitLab, Stripe, and generic signing secret. Fresh holdout groups: Google, Mailgun,
and generic integration password. Use 100 examples per label per group (2,400
rows) and seed 20261001. Exact values and source contexts must be unique across
groups and disjoint from the old dataset when available.

Negatives are invented offline fixtures or dummy configuration, not harvested
credentials. A fixture that looks like a provider token can have exactly the same
numeric features as a positive. This ambiguity is intentional and must be
reported, not eliminated by relabeling. Half of generic negative examples use a
dummy prefix; other negatives retain random credential-shaped values. Review is
local template inspection, not independent human adjudication or real validity.

Train on actual scanner candidate spans using unchanged feature version 1. Require
both positive and negative extracted candidates in training and validation.
Compare a newly fitted random forest with XGBoost (CPU histogram method, one
thread, seed fixed, 100 estimators, learning rate 0.1, depths 3 and 6). Forest uses
the existing three fixed configurations. Both select using validation F2, recall,
precision, then distance from threshold 0.5, over 0.25/0.4/0.5/0.6/0.75. No refit
on validation and no early stopping on test. Freeze both selections before
constructing/evaluating the holdout. Record rules, regex, both hypothetical model
filters, confusion matrices, per-group errors, coverage, provenance, dependency
versions, timings, and checksums. The CLI keeps every candidate whatever the
outcome; there is no calibration or production promotion in this sprint.

Historical error analysis uses the existing aggregate baseline report, never
individual credentials or source snippets. The fourth notebook displays aggregate
error counts and limitations only. Synthetic results do not establish performance
on unseen real repositories. Once evaluated, this holdout is observed and cannot
serve as a fresh tuning holdout for later experiments.
