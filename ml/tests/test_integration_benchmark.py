"""Frozen-model integration reproduction and aggregate-only figure export."""

import json
import subprocess
import sys

import pytest

from ml.scripts.benchmark_pipeline import run as benchmark
from ml.scripts.plot_benchmarks import render
from ml.scripts.train_baseline import run as train
from ml.tests.test_baseline import write_dataset


def test_integrated_reproduction_and_figures(tmp_path):
    rows = write_dataset(tmp_path)
    baseline = train(tmp_path, tmp_path)
    digest = baseline["artifact"]["sha256"]
    report_path = tmp_path / "baseline.json"
    model_path = tmp_path / "baseline.pkl"
    result = benchmark(tmp_path, report_path, model_path, expected_sha256=digest)
    assert result["frozen_baseline_agreement"]
    assert (
        result["metrics"]["retained_candidates"]
        == baseline["evaluation"]["test"]["metrics"]["rules_and_entropy"]
    )
    assert result["candidates"]["retained"] >= result["candidates"]["above_threshold"]
    assert all(row["value"] not in json.dumps(result) for row in rows)
    outputs = render(report_path, tmp_path / "figures")
    assert len(outputs) == 4
    assert all(path.stat().st_size > 1000 for path in outputs)
    for path in outputs:
        if path.suffix == ".svg":
            assert all(row["value"] not in path.read_text() for row in rows)
            assert "synthetic" in path.read_text().lower()
    with pytest.raises(ValueError, match="does not match"):
        benchmark(tmp_path, report_path, model_path, expected_sha256="0" * 64)
    baseline["selection"]["selected"]["threshold"] = -1
    report_path.write_text(json.dumps(baseline))
    with pytest.raises(ValueError, match="threshold"):
        benchmark(tmp_path, report_path, model_path, expected_sha256=digest)
    baseline["selection"]["selected"]["threshold"] = result["threshold"]
    baseline["evaluation"]["test"]["metrics"]["rules_and_entropy"]["rows"] += 1
    report_path.write_text(json.dumps(baseline))
    with pytest.raises(ValueError, match="disagrees"):
        benchmark(tmp_path, report_path, model_path, expected_sha256=digest)


@pytest.mark.parametrize(
    "module,args",
    [
        ("benchmark_pipeline", ["--model-sha256", "0" * 64, "--data-dir"]),
        ("plot_benchmarks", ["--report"]),
    ],
)
def test_tools_fail_without_input_leaks(tmp_path, module, args):
    process = subprocess.run(
        [sys.executable, "-m", f"ml.scripts.{module}", *args, str(tmp_path / "missing")],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert process.returncode == 2
    assert "Traceback" not in process.stderr
    assert str(tmp_path) not in process.stderr
