"""Offline experiment integrity, aggregate reporting, and notebook smoke tests."""

import csv
import io
import json
import os
import subprocess
import sys

import pytest
from secretsense.features import FEATURE_NAMES

from ml.scripts.build_dataset import ROOT, build
from ml.scripts.train_baseline import candidate_scores, features, read_dataset, run


def write_dataset(path):
    data, manifest = build(count=5)
    (path / "dataset.csv").write_bytes(data)
    (path / "manifest.json").write_text(json.dumps(manifest))
    return list(csv.DictReader(io.StringIO(data.decode())))


def test_metadata_exclusion():
    value = "Ab9" * 8
    row = {"value": value, "text": f'password = "{value}"'}
    poisoned = {**row, "label": 1, "split": "test", "category": "positive", "sample_id": value}
    assert features([row]) == features([poisoned])
    assert len(features([row])[0]) == len(FEATURE_NAMES)


def test_dataset_checksum_and_row_count(tmp_path):
    write_dataset(tmp_path)
    read_dataset(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["rows"] += 1
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="count mismatch"):
        read_dataset(tmp_path)
    (tmp_path / "dataset.csv").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum mismatch"):
        read_dataset(tmp_path)


def test_candidate_boundaries_and_missing_candidate():
    class Model:
        def predict_proba(self, vectors):
            import numpy as np

            # A private-key candidate contains only the header, not the full annotation.
            assert vectors[0][FEATURE_NAMES.index("has_newline")] == 0
            return np.array([[0.2, 0.8]] * len(vectors))

    header = "-----BEGIN " + "PRIVATE KEY-----"
    value = header + "\n" + "invented-body"
    scores, covered = candidate_scores(Model(), [{"text": value}, {"text": "nothing here"}])
    assert scores == [0.8, -1.0]
    assert covered == [True, False]
    assert candidate_scores(Model(), [{"text": "nothing here"}]) == ([-1.0], [False])


def test_run_isolation_aggregate_privacy_and_notebooks(tmp_path, monkeypatch):
    from ml.scripts import train_baseline

    rows = write_dataset(tmp_path)
    original = train_baseline.select_model
    calls = []

    def select(train_x, train_y, validation_x, validation_y):
        assert train_x == features([row for row in rows if row["split"] == "train"])
        assert validation_x == features([row for row in rows if row["split"] == "validation"])
        calls.append("selection")
        return original(train_x, train_y, validation_x, validation_y)

    monkeypatch.setattr(train_baseline, "select_model", select)
    result = run(tmp_path, tmp_path)
    assert calls == ["selection"]
    assert result["evaluation"]["test"]["metrics"]["regex_only"]["rows"] == 20
    report = json.dumps(result)
    assert all(row["value"] not in report and row["text"] not in report for row in rows)
    assert result["evaluation"]["train"]["candidate_coverage"]["0"]["rows_with_candidates"] == 0
    # Exact reruns must agree on model bytes and quality results, not wall time.
    repeat = run(tmp_path, tmp_path)
    assert repeat["artifact"] == result["artifact"]
    assert repeat["evaluation"] == result["evaluation"]
    for name in ("02_features.ipynb", "03_model_comparison.ipynb"):
        notebook = json.loads((ROOT / "notebooks" / name).read_text())
        code = "\n".join(
            "".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"
        )
        runner = tmp_path / "notebook.py"
        runner.write_text(code)
        process = subprocess.run(
            [sys.executable, str(runner)],
            cwd=ROOT.parent,
            env={
                **os.environ,
                "SECRETSENSE_DATA_DIR": str(tmp_path),
                "SECRETSENSE_RESULTS_DIR": str(tmp_path),
                "PYTHONPATH": str(ROOT.parent),
            },
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert process.returncode == 0, "Notebook execution failed; output omitted."
        assert all(row["value"] not in process.stdout + process.stderr for row in rows)


def test_cli_safe_failure(tmp_path):
    process = subprocess.run(
        [sys.executable, "-m", "ml.scripts.train_baseline", "--data-dir", str(tmp_path)],
        cwd=ROOT.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert process.returncode == 2
    assert "Traceback" not in process.stderr
