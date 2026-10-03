# Sprint 8 LLM benefit experiment protocol

This protocol is fixed before the first run. Do not change the prompt, model, groups,
seed, counts, or metrics in response to outcomes. The resulting set is observed after
one run and cannot serve as a fresh holdout again. It is disjoint from the sprint 5
holdout groups and uses a new seed.

**Question.** Does the shipped advisory review (`--llm`, unchanged prompt) separate
benign generic candidates from credential-shaped ones better than keeping every
candidate? Verdicts never suppress findings, so this measures what a reviewer could
safely deprioritize, not a production filter.

**Model and settings.** `qwen2.5:3b` through a local Ollama server, temperature 0,
the shipped prompt and advisor unchanged, 60-second timeout. One run with no retries; a failed review is counted as `error`.

**Data.** Synthetic only; seed 20261101; three independently authored groups, each in
its own file style: `deploy-yaml`, `env-settings`, `python-settings`. Each group has
60 positives and 60 negatives (120 per group, 360 total). Positives use a realistic
secret-style key name and a random 32–48 character value. Negatives are split evenly:

- `cue-name`: random value, key name or trailing comment visibly marks an example,
  fixture, or sample.
- `placeholder-value`: a value that spells out a placeholder instruction.
- `no-cue`: random value under a realistic key name, identical in visible shape to
  positives. These are **indistinguishable by construction** and are reported
  separately; they are not removed or relabeled.

Values and rows must be unique and disjoint from the historical corpus when present.

**Metrics.** Only rows whose generic candidate is extracted are reviewed. Report:
candidate coverage per label; verdict counts per label and per negative kind;
baseline (keep everything) precision; precision and recall when `likely-placeholder`
is treated as deprioritized (`likely-secret` and `unsure` kept); the same with
`unsure` also deprioritized; per-group and per-negative-kind breakdowns; error count;
elapsed time. Aggregates only: no values or source lines are written.

**Limits.** Synthetic data, one small model, one run, authored by the same team as the
detector. Results do not establish performance on real repositories or other models.
