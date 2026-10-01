"""Reproduce a frozen baseline through the installed scanner; never tune or train."""

import argparse
import hashlib
import json
import platform
import time
from dataclasses import replace
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from secretsense.model.predict import LocalPredictor
from secretsense.model.train import metrics
from secretsense.scanner.engine import scan_text

from ml.scripts.build_dataset import ROOT
from ml.scripts.train_baseline import read_dataset, source_state


def run(data_dir: Path, baseline_path: Path, model_path: Path, *, expected_sha256: str) -> dict:
    rows, manifest = read_dataset(data_dir)
    baseline_bytes = baseline_path.read_bytes()
    baseline = json.loads(baseline_bytes)
    if (
        baseline["dataset_sha256"] != manifest["dataset_sha256"]
        or baseline["artifact"]["sha256"] != expected_sha256
    ):
        raise ValueError("Benchmark dataset or artifact does not match the recorded baseline.")
    predictor = LocalPredictor.load(model_path, expected_sha256=expected_sha256)
    if predictor.threshold != baseline["selection"]["selected"]["threshold"]:
        raise ValueError("Benchmark threshold does not match the recorded baseline.")
    truth, retained, above = [], [], []
    candidate_count = above_count = 0
    started = time.perf_counter()
    for row in rows:
        if row["split"] != "test":
            continue
        findings = scan_text(row["text"], predictor=predictor)
        rules = scan_text(row["text"])
        if [replace(item, model_score=None, model_decision=None) for item in findings] != rules:
            raise ValueError("Integrated scoring changed scanner findings.")
        truth.append(int(row["label"]))
        retained.append(int(bool(findings)))
        above.append(int(any(item.model_decision == "above-threshold" for item in findings)))
        candidate_count += len(findings)
        above_count += sum(item.model_decision == "above-threshold" for item in findings)
    results = {
        "retained_candidates": metrics(truth, retained),
        "above_threshold_only": metrics(truth, above),
    }
    recorded = baseline["evaluation"]["test"]["metrics"]
    if (
        results["retained_candidates"] != recorded["rules_and_entropy"]
        or results["above_threshold_only"] != recorded["candidate_pipeline_model"]
    ):
        raise ValueError("Integrated benchmark disagrees with the frozen baseline.")
    return {
        "schema_version": 1,
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "baseline_report_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
        "dataset_sha256": manifest["dataset_sha256"],
        "artifact_sha256": expected_sha256,
        "threshold": predictor.threshold,
        "policy": "annotate-all-candidates",
        "metrics": results,
        "candidates": {
            "retained": candidate_count,
            "above_threshold": above_count,
            "below_threshold": candidate_count - above_count,
        },
        "frozen_baseline_agreement": True,
        "environment": {
            "python": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
            "scikit-learn": version("scikit-learn"),
        },
        "source_state": source_state(),
        "scan_comparison_seconds": time.perf_counter() - started,
        "limitations": [
            "Reproduction on the already observed synthetic test split, not a new evaluation.",
            "Above-threshold-only metrics describe hypothetical filtering; "
            "CLI retains all findings.",
            "Scores are uncalibrated and do not establish credential validity.",
            "Single-run timing includes both scored and rules scans; not a latency benchmark.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--baseline", type=Path, default=ROOT / "results" / "baseline.json")
    parser.add_argument("--model", type=Path, default=ROOT / "results" / "baseline.pkl")
    parser.add_argument("--model-sha256", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "integration.json")
    args = parser.parse_args()
    try:
        result = run(args.data_dir, args.baseline, args.model, expected_sha256=args.model_sha256)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except Exception:
        parser.exit(
            2, "Integration benchmark failed; check trusted artifacts and dataset integrity.\n"
        )
    print("Frozen baseline reproduced through the scanner; aggregate report written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
