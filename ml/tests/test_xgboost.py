"""Fresh-group integrity, selection isolation, reproduction, and aggregate privacy."""

import json

import pytest

pytest.importorskip("xgboost")

from ml.scripts import evaluate_xgboost as experiment


def test_generation_isolation_and_candidate_negatives():
    rows = sum((experiment.generate_split(split, 5) for split in experiment.GROUPS), [])
    experiment.validate_isolation(rows)
    assert rows == sum((experiment.generate_split(split, 5) for split in experiment.GROUPS), [])
    for split in experiment.GROUPS:
        _, labels = experiment.candidate_training([row for row in rows if row["split"] == split])
        assert set(labels) == {0, 1}
    with pytest.raises(ValueError, match="Duplicate"):
        experiment.validate_isolation(rows + rows[:1])
    with pytest.raises(ValueError, match="overlaps"):
        experiment.validate_isolation(rows, {rows[0]["value"]})
    with pytest.raises(ValueError, match="crosses"):
        experiment.validate_isolation([rows[0], {**rows[1], "split": "test"}])
    with pytest.raises(ValueError):
        experiment.generate_split("test", 0)
    with pytest.raises(ValueError, match="both labels"):
        experiment.candidate_training([row for row in rows if row["label"] == 1])


def test_freeze_before_holdout_and_reproduction(tmp_path, monkeypatch):
    calls = []
    original_generate = experiment.generate_split
    original_forest = experiment.select_model
    original_xgb = experiment.select_xgboost

    def forest(*args, **kwargs):
        result = original_forest(*args, **kwargs)
        calls.append("forest-frozen")
        return result

    def xgb(*args, **kwargs):
        result = original_xgb(*args, **kwargs)
        calls.append("xgb-frozen")
        return result

    def generate(split, count):
        if split == "test":
            assert calls[-2:] == ["forest-frozen", "xgb-frozen"]
        return original_generate(split, count)

    monkeypatch.setattr(experiment, "select_model", forest)
    monkeypatch.setattr(experiment, "select_xgboost", xgb)
    monkeypatch.setattr(experiment, "generate_split", generate)
    report = experiment.run(tmp_path, count=5)
    repeat = experiment.run(tmp_path, count=5)
    assert report["evaluation"] == repeat["evaluation"]
    assert report["selection"] == repeat["selection"]
    assert report["artifact"] == repeat["artifact"]
    assert not report["historical_value_disjointness_checked"]
    serialized = json.dumps(report)
    for split in experiment.GROUPS:
        assert all(
            row["value"] not in serialized and row["text"] not in serialized
            for row in original_generate(split, 5)
        )
    assert report["evaluation"]["test"]["metrics"]["xgboost_filter"]["rows"] == 30


def test_error_notebook_executes_without_values(tmp_path, capsys):
    # The notebook consumes only aggregates, so it needs no corpus or model.
    from pathlib import Path

    notebook = json.loads(
        (Path(__file__).parents[1] / "notebooks" / "04_error_analysis.ipynb").read_text()
    )
    namespace = {}
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            exec("".join(cell["source"]), namespace)
    output = capsys.readouterr().out
    assert "Historical errors" in output
    assert "false_negatives" in output
    assert all(row["value"] not in output for row in experiment.generate_split("test"))
