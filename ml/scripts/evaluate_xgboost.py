"""Fresh grouped synthetic candidate experiment. Reports contain aggregates only."""

import argparse
import hashlib
import json
import platform
import time
from collections import Counter
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from secretsense.features import FEATURE_NAMES, FEATURE_VERSION, extract_features
from secretsense.model.train import THRESHOLDS, metrics, select_model
from secretsense.scanner.candidates import extract_candidates
from secretsense.scanner.patterns import RULES

from ml.scripts.common import family_rng, random_text
from ml.scripts.train_baseline import ROOT, candidate_scores, labels, source_state

SEED = 20261001
# Paired positive/negative source templates remain in the same split.
GROUPS = {
    "train": (
        "github-client",
        "aws-worker",
        "database-login",
        "npm-publish",
        "slack-bot",
        "session-token",
    ),
    "validation": ("gitlab-project", "stripe-billing", "signing-secret"),
    "test": ("google-maps", "mailgun-sender", "integration-password"),
}


def value_for(group, rng):
    if group == "github-client":
        return "ghp_" + random_text(rng, 36)
    if group == "aws-worker":
        return "AKIA" + random_text(rng, 16, "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    if group == "npm-publish":
        return "npm_" + random_text(rng, 36)
    if group == "slack-bot":
        return "xoxb-" + random_text(rng, 40)
    if group == "gitlab-project":
        return "glpat-" + random_text(rng, 20)
    if group == "stripe-billing":
        return "sk_" + "test_" + random_text(rng, 32)
    if group == "google-maps":
        return "AIza" + random_text(rng, 35)
    if group == "mailgun-sender":
        return "key-" + random_text(rng, 32, "0123456789abcdef")
    return random_text(rng, 36)


def generate_split(split: str, count: int = 100) -> list[dict]:
    if split not in GROUPS or not 1 <= count <= 1000:
        raise ValueError("Invalid experiment split or count.")
    rows = []
    for group in GROUPS[split]:
        rng = family_rng(SEED, "sprint5:" + group)
        for label in (0, 1):
            for index in range(count):
                value = value_for(group, rng)
                if (
                    label == 0
                    and group
                    in {"database-login", "session-token", "signing-secret", "integration-password"}
                    and index % 2 == 0
                ):
                    value = "dummy_" + value
                # Labels/provenance do not become features. Both contexts use a
                # secret-like name, so feature equality across labels is expected.
                role = (
                    "application configuration"
                    if label
                    else "offline parser fixture; never provisioned"
                )
                text = f'# {role}\n{group.replace("-", "_")}_api_token = "{value}"\n'
                rows.append(
                    {
                        "text": text,
                        "value": value,
                        "label": label,
                        "template_family": group,
                        "source_group": "sprint5:" + group,
                        "split": split,
                    }
                )
    return rows


def validate_isolation(rows: list[dict], old_values: set[str] | None = None) -> None:
    if len({row["value"] for row in rows}) != len(rows) or len(
        {row["text"] for row in rows}
    ) != len(rows):
        raise ValueError("Duplicate experiment input; content omitted.")
    if old_values and any(row["value"] in old_values for row in rows):
        raise ValueError("Experiment overlaps the historical corpus; content omitted.")
    for group in {row["source_group"] for row in rows}:
        if len({row["split"] for row in rows if row["source_group"] == group}) != 1:
            raise ValueError("Experiment source group crosses splits.")


def candidate_training(rows: list[dict]):
    vectors, truth = [], []
    for row in rows:
        for candidate in extract_candidates(row["text"]):
            vectors.append(
                extract_features(
                    row["text"][candidate.start : candidate.end],
                    row["text"],
                    value_start=candidate.start,
                )
            )
            truth.append(row["label"])
    if set(truth) != {0, 1}:
        raise ValueError("Candidate training requires both labels.")
    return vectors, truth


def select_xgboost(train_x, train_y, validation_x, validation_y):
    from xgboost import XGBClassifier

    best, trials = None, []
    for depth in (3, 6):
        model = XGBClassifier(
            n_estimators=100,
            max_depth=depth,
            learning_rate=0.1,
            tree_method="hist",
            n_jobs=1,
            random_state=SEED,
            objective="binary:logistic",
            eval_metric="logloss",
        )
        model.fit(train_x, train_y)
        scores = model.predict_proba(validation_x)[:, 1]
        for threshold in THRESHOLDS:
            measured = metrics(validation_y, scores >= threshold)
            trial = {
                "parameters": {"max_depth": depth, "n_estimators": 100, "learning_rate": 0.1},
                "threshold": threshold,
                "metrics": measured,
            }
            trials.append(trial)
            rank = (
                measured["f2"],
                measured["recall"],
                measured["precision"],
                -abs(threshold - 0.5),
            )
            if best is None or rank > best[0]:
                best = (rank, model, trial)
    return best[1], {"selected": best[2], "trials": trials, "seed": SEED}


def evaluate(rows, models):
    truth = labels(rows)
    coverage = [bool(extract_candidates(row["text"])) for row in rows]
    predictions = {
        "regex_only": [
            int(any(rule.pattern.search(row["text"]) for rule in RULES)) for row in rows
        ],
        "rules_and_entropy": [int(hit) for hit in coverage],
    }
    for name, (model, threshold) in models.items():
        scores, _ = candidate_scores(model, rows)
        predictions[name] = [int(score >= threshold) for score in scores]
    return {
        "metrics": {name: metrics(truth, predicted) for name, predicted in predictions.items()},
        "candidate_coverage": {
            str(label): {
                "rows": truth.count(label),
                "rows_with_candidates": sum(
                    hit for hit, actual in zip(coverage, truth, strict=True) if actual == label
                ),
            }
            for label in (0, 1)
        },
        "by_family": {
            group: {
                name: metrics([truth[i] for i in indices], [predicted[i] for i in indices])
                for name, predicted in predictions.items()
            }
            for group in sorted({row["template_family"] for row in rows})
            for indices in [[i for i, row in enumerate(rows) if row["template_family"] == group]]
        },
    }


def historical_errors(path: Path) -> dict:
    baseline = json.loads(path.read_text())
    return {
        "baseline_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "by_family": {
            family: {
                method: {
                    "false_positives": result["confusion_matrix"][0][1],
                    "false_negatives": result["confusion_matrix"][1][0],
                }
                for method, result in methods.items()
            }
            for family, methods in baseline["evaluation"]["test"]["by_family"].items()
        },
    }


def run(output: Path, *, count: int = 100, historical_data: Path | None = None) -> dict:
    start = time.perf_counter()
    train, validation = generate_split("train", count), generate_split("validation", count)
    validate_isolation(train + validation)
    train_x, train_y = candidate_training(train)
    val_x, val_y = candidate_training(validation)
    forest, forest_selection = select_model(train_x, train_y, val_x, val_y, seed=SEED)
    booster, booster_selection = select_xgboost(train_x, train_y, val_x, val_y)
    # Both choices are frozen before holdout construction, access, or scoring.
    models = {
        "random_forest_filter": (forest, forest_selection["selected"]["threshold"]),
        "xgboost_filter": (booster, booster_selection["selected"]["threshold"]),
    }
    test = generate_split("test", count)
    all_rows = train + validation + test
    old_values = None
    old_digest = None
    if historical_data is not None:
        from ml.scripts.train_baseline import read_dataset

        old_rows, old_manifest = read_dataset(historical_data)
        old_values = {row["value"] for row in old_rows}
        old_digest = old_manifest["dataset_sha256"]
    validate_isolation(all_rows, old_values)
    dataset_digest = hashlib.sha256(json.dumps(all_rows, sort_keys=True).encode()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    artifact = output / "xgboost.ubj"
    booster.save_model(artifact)
    from xgboost import XGBClassifier

    restored = XGBClassifier()
    restored.load_model(artifact)
    if not (restored.predict_proba(val_x) == booster.predict_proba(val_x)).all():
        raise ValueError("XGBoost artifact round trip changed validation predictions.")
    results = {
        split: evaluate(rows, models)
        for split, rows in (("train", train), ("validation", validation), ("test", test))
    }
    result = {
        "schema_version": 1,
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "seed": SEED,
        "examples_per_label_per_group": count,
        "rows": len(all_rows),
        "dataset_sha256": dataset_digest,
        "historical_dataset_sha256": old_digest,
        "historical_value_disjointness_checked": old_values is not None,
        "split_groups": GROUPS,
        "feature_version": FEATURE_VERSION,
        "feature_names": FEATURE_NAMES,
        "training_population": "Actual scanner spans; both labels present in every split.",
        "selection_policy": (
            "Validation F2, recall, precision, distance from 0.5; no refit; "
            "both selections frozen before test generation."
        ),
        "selection": {"random_forest": forest_selection, "xgboost": booster_selection},
        "evaluation": results,
        "candidate_training_labels": dict(Counter(str(label) for label in train_y)),
        "artifact": {
            "filename": artifact.name,
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            "format": "xgboost-ubj-evaluation-only",
        },
        "historical_errors": historical_errors(ROOT / "results" / "baseline.json"),
        "source_state": source_state(),
        "protocol_sha256": hashlib.sha256(
            (ROOT.parent / "docs" / "sprint5-experiment.md").read_bytes()
        ).hexdigest(),
        "environment": {
            "python": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
            "dependencies": {
                name: version(name)
                for name in ("xgboost", "scikit-learn", "numpy", "scipy", "joblib", "threadpoolctl")
            },
        },
        "total_seconds": time.perf_counter() - start,
        "limitations": [
            "Invented synthetic intent labels; no validity or real-world performance claim.",
            "Independent new templates, not independent human adjudication.",
            "Some opposite-label features are indistinguishable; scores cannot resolve intent.",
            "Uncalibrated scores; hypothetical filtering only. CLI retains every candidate.",
            "This holdout is now observed; later tuning requires a new reserved holdout.",
        ],
    }
    (output / "xgboost.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--historical-data", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    try:
        result = run(args.output_dir, historical_data=args.historical_data)
    except (OSError, ValueError, KeyError, ImportError):
        parser.exit(2, "Experiment failed: check local data, dependencies, and permissions.\n")
    print("Fresh grouped synthetic experiment completed; aggregate report written.")
    print(json.dumps(result["evaluation"]["test"]["metrics"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
