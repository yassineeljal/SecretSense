"""Train and evaluate the synthetic baseline locally; emit aggregate results only."""

import argparse
import csv
import hashlib
import io
import json
import platform
import subprocess
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from secretsense.features import FEATURE_NAMES, FEATURE_VERSION, extract_features
from secretsense.model.artifact import load_trusted_artifact, save_artifact
from secretsense.model.train import metrics, select_model
from secretsense.scanner.candidates import extract_candidates
from secretsense.scanner.patterns import RULES

from ml.scripts.build_dataset import ROOT, validate_rows


def read_dataset(directory: Path) -> tuple[list[dict], dict]:
    data = (directory / "dataset.csv").read_bytes()
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if hashlib.sha256(data).hexdigest() != manifest["dataset_sha256"]:
        raise ValueError("Dataset checksum mismatch.")
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    validate_rows(rows)
    if len(rows) != manifest["rows"]:
        raise ValueError("Dataset count mismatch.")
    return rows, manifest


def features(rows: list[dict]) -> list[tuple[float, ...]]:
    # The explicit two-argument interface prevents metadata becoming features.
    return [extract_features(row["value"], row["text"]) for row in rows]


def labels(rows: list[dict]) -> list[int]:
    return [int(row["label"]) for row in rows]


def candidate_scores(model, rows: list[dict]) -> tuple[list[float], list[bool]]:
    vectors, owners = [], []
    covered = [False] * len(rows)
    for index, row in enumerate(rows):
        for candidate in extract_candidates(row["text"]):
            covered[index] = True
            vectors.append(
                extract_features(
                    row["text"][candidate.start : candidate.end],
                    row["text"],
                    value_start=candidate.start,
                )
            )
            owners.append(index)
    scores = [-1.0] * len(rows)  # No candidate always means a negative prediction.
    if vectors:
        for index, score in zip(owners, model.predict_proba(vectors)[:, 1], strict=True):
            scores[index] = max(scores[index], float(score))
    return scores, covered


def evaluate(model, threshold: float, rows: list[dict]) -> dict:
    truth = labels(rows)
    scores, covered = candidate_scores(model, rows)
    predictions = {
        "regex_only": [
            int(any(rule.pattern.search(row["text"]) for rule in RULES)) for row in rows
        ],
        "rules_and_entropy": [int(item) for item in covered],
        "annotated_value_model": (model.predict_proba(features(rows))[:, 1] >= threshold)
        .astype(int)
        .tolist(),
        "candidate_pipeline_model": [int(score >= threshold) for score in scores],
    }
    return {
        "metrics": {name: metrics(truth, prediction) for name, prediction in predictions.items()},
        "candidate_coverage": {
            str(label): {
                "rows": truth.count(label),
                "rows_with_candidates": sum(
                    hit for hit, actual in zip(covered, truth, strict=True) if actual == label
                ),
            }
            for label in (0, 1)
        },
        "by_family": {
            family: {
                name: metrics(
                    [truth[index] for index in indices],
                    [prediction[index] for index in indices],
                )
                for name, prediction in predictions.items()
            }
            for family in sorted({row["template_family"] for row in rows})
            for indices in [[i for i, row in enumerate(rows) if row["template_family"] == family]]
        },
    }


def source_state() -> dict:
    root = ROOT.parent
    paths = sorted((root / "core" / "secretsense").rglob("*.py")) + sorted(
        (ROOT / "scripts").glob("*.py")
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=False
    )
    return {
        "git_head": commit.stdout.strip() if commit.returncode == 0 else "unavailable",
        "working_tree_dirty": bool(status.stdout) if status.returncode == 0 else None,
        "sources": [
            {
                "path": str(path.relative_to(root)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in paths
        ],
    }


def run(data_dir: Path, output_dir: Path) -> dict:
    start = time.perf_counter()
    rows, manifest = read_dataset(data_dir)
    splits = {
        name: [row for row in rows if row["split"] == name]
        for name in ("train", "validation", "test")
    }
    # Selection cannot access test inputs, labels, or predictions.
    model, selection = select_model(
        features(splits["train"]),
        labels(splits["train"]),
        features(splits["validation"]),
        labels(splits["validation"]),
    )
    threshold = selection["selected"]["threshold"]
    fit_seconds = time.perf_counter() - start
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / "baseline.pkl"
    digest = save_artifact(model, threshold, artifact)
    restored = load_trusted_artifact(artifact, expected_sha256=digest)
    validation_x = features(splits["validation"])
    if not (
        model.predict_proba(validation_x) == restored["model"].predict_proba(validation_x)
    ).all():
        raise ValueError("Artifact round-trip changed validation predictions.")
    # Test evaluation begins only after the model and threshold have been frozen.
    evaluation = {name: evaluate(model, threshold, split) for name, split in splits.items()}
    result = {
        "schema_version": 1,
        "trained_at_utc": datetime.now(UTC).isoformat(),
        "dataset_sha256": manifest["dataset_sha256"],
        "dataset_manifest_sha256": hashlib.sha256(
            (data_dir / "manifest.json").read_bytes()
        ).hexdigest(),
        "artifact": {
            "filename": "baseline.pkl",
            "sha256": digest,
            "format": "trusted-local-pickle-protocol-5",
        },
        "feature_version": FEATURE_VERSION,
        "feature_names": FEATURE_NAMES,
        "feature_importances": dict(
            zip(FEATURE_NAMES, model.feature_importances_.tolist(), strict=True)
        ),
        "training_population": (
            "All annotated values; candidate-only training lacks negative examples."
        ),
        "selection_policy": (
            "Validation F2, then recall, precision, threshold closest to 0.5; "
            "first configuration wins remaining ties. No train+validation refit."
        ),
        "selection": selection,
        "evaluation": evaluation,
        "environment": {
            "python": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "dependencies": {
                name: version(name)
                for name in ("scikit-learn", "numpy", "scipy", "joblib", "threadpoolctl")
            },
        },
        "source_state": source_state(),
        "timing_seconds": {"fit_and_selection": fit_seconds, "total": time.perf_counter() - start},
        "limitations": [
            "Synthetic grouped holdout only; no real-world accuracy or credential validity claim.",
            "Training/validation candidate negatives are absent for the default corpus.",
            "Annotated-value evaluation assumes supplied boundaries; "
            "pipeline evaluation uses actual scanner spans.",
            "Scores are uncalibrated; the CLI uses the threshold only for opt-in annotations.",
            "Only twenty families; validation cannot measure candidate false-positive suppression.",
            "Test results must not be used to retune this baseline; "
            "new experiments need a fresh holdout.",
        ],
    }
    (output_dir / "baseline.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    try:
        result = run(args.data_dir, args.output_dir)
    except (OSError, ValueError, KeyError, TypeError, csv.Error):
        parser.exit(
            2,
            "Baseline failed: check dataset integrity, ML dependencies, and output permissions.\n",
        )
    print("Local synthetic baseline completed; aggregate report written.")
    print(f"Artifact SHA-256: {result['artifact']['sha256']}")
    print(json.dumps(result["evaluation"]["test"]["metrics"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
