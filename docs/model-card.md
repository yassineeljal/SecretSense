# Model card

Status: **no trained model exists yet**. The current release uses deterministic
rules and entropy. Severity labels are not probabilities. No accuracy, precision,
recall, or F1 claim has been established.

The planned baseline is a local scikit-learn random forest, with XGBoost evaluated
later. The dataset target is 5,000–20,000 balanced examples from synthetic
credential shapes, invented configuration passwords, and non-secret examples.
Training, validation, and test splits must be grouped by source repository or
synthetic template family to reduce leakage.

Evaluation will prioritize recall while reporting precision, recall, F1, a
confusion matrix, per-service results, and performance on unseen repositories.
Synthetic keys differ from real-world leaks, labels can be ambiguous, and service
formats change. The model card must record provenance, intended use, exclusions,
training date, artifact hash, license, split strategy, and observed failure cases
before a model ships. Untrusted pickle files must never be loaded.
