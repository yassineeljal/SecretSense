"""Prediction, privacy, and report contracts using runtime synthetic inputs."""

import hashlib
import json
import os
import pickle
import subprocess
import sys
import warnings
from dataclasses import replace
from html.parser import HTMLParser

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier
from typer.testing import CliRunner

from secretsense.cli import app
from secretsense.features import FEATURE_NAMES, extract_features
from secretsense.model.artifact import load_trusted_artifact, save_artifact
from secretsense.model.predict import LocalPredictor, PredictionError
from secretsense.report.console import render_console
from secretsense.report.html_report import render_html
from secretsense.report.json_report import render_json
from secretsense.scanner.engine import ScanReport, scan_path, scan_text


@pytest.fixture
def artifact(tmp_path):
    model = RandomForestClassifier(n_estimators=2, random_state=4).fit(
        [[0.0] * len(FEATURE_NAMES), [1.0] * len(FEATURE_NAMES)], [0, 1]
    )
    path = tmp_path / "model.pkl"
    digest = save_artifact(model, 0.6, path)
    return path, digest


class FixedModel:
    def __init__(self, score):
        self.score = score
        self.batches = []

    def predict_proba(self, vectors):
        self.batches.append(len(vectors))
        return np.array([[1 - self.score, self.score]] * len(vectors))


@pytest.mark.parametrize(
    "score,decision", [(0.0, "below-threshold"), (0.6, "above-threshold"), (1.0, "above-threshold")]
)
def test_scores_never_filter_or_change_severity(score, decision):
    value = "ghp_" + "Ab3x" * 9
    content = f'token = "{value}"'
    predictor = LocalPredictor(FixedModel(score), 0.6, "a" * 64)
    findings = scan_text(content, predictor=predictor)
    assert len(findings) == 1
    assert findings[0].model_score == score
    assert findings[0].model_decision == decision
    assert replace(findings[0], model_score=None, model_decision=None) == scan_text(content)[0]
    report = ScanReport(findings=findings, model={"threshold": 0.6})
    for output in (
        repr(findings),
        render_json(report),
        render_console(report),
        render_html(report),
    ):
        assert value not in output
    assert json.loads(render_json(report))["schema_version"] == "1.3"


def test_empty_candidates_and_bounded_batches():
    model = FixedModel(0.1)
    predictor = LocalPredictor(model, 0.6, "a" * 64)
    assert scan_text("nothing here", predictor=predictor) == []
    assert model.batches == []
    value = "ghp_" + "Ab3x" * 9
    assert len(scan_text((value + "\n") * 257, predictor=predictor)) == 257
    assert model.batches == [256, 1]


def test_repeated_values_use_correct_occurrence():
    value = "ghp_" + "Ab3x" * 9
    content = f'build_id = "{value}"\n' + " " * 210 + f'token = "{value}"'
    start = content.rindex(value)
    index = FEATURE_NAMES.index("secret_name")
    assert extract_features(value, content)[index] == 0
    assert extract_features(value, content, value_start=start)[index] == 1
    with pytest.raises(ValueError, match="offset"):
        extract_features(value, content, value_start=-1)

    class ContextModel:
        def predict_proba(self, vectors):
            assert [vector[index] for vector in vectors] == [0, 1]
            return [[0.8, 0.2], [0.2, 0.8]]

    assert [
        item.model_score
        for item in scan_text(content, predictor=LocalPredictor(ContextModel(), 0.6, "a" * 64))
    ] == [0.2, 0.8]


@pytest.mark.parametrize(
    "invalid", [[], [[0.1]], [[float("nan"), 0.5]], [[-0.1, 1.1]], [[0.2, 0.2]], "raise", "warn"]
)
def test_prediction_failure_preserves_findings_and_redacts_errors(tmp_path, invalid):
    value = "ghp_" + "Ab3x" * 9
    target = tmp_path / "input.txt"
    target.write_text(value)

    class BadModel:
        def predict_proba(self, vectors):
            if invalid == "raise":
                raise RuntimeError(value)
            if invalid == "warn":
                warnings.warn(value, stacklevel=1)
            return invalid

    predictor = LocalPredictor(BadModel(), 0.6, "a" * 64)
    with pytest.raises(PredictionError) as error:
        scan_text(value, predictor=predictor)
    assert value not in str(error.value)
    report = scan_path(target, predictor=predictor)
    assert not report.complete
    assert report.files_scanned == 1
    assert report.findings == scan_text(value, target.name)
    assert value not in render_json(report)


@pytest.mark.parametrize("format", ["console", "json", "html"])
def test_cli_trusted_model_and_all_formats(tmp_path, artifact, format):
    path, digest = artifact
    value = "AKIA" + "A1" * 8
    target = tmp_path / "input.txt"
    target.write_text(value)
    result = CliRunner().invoke(
        app, ["scan", str(target), "-f", format, "--model", str(path), "--model-sha256", digest]
    )
    assert result.exit_code == 1
    assert value not in result.output
    if format == "json":
        report = json.loads(result.stdout)
        assert report["engine"] == "rules-and-entropy+local-ml"
        assert report["model"]["sha256"] == digest
        assert report["model"]["policy"] == "annotate-all-candidates"
        assert report["findings"][0]["model_score"] is not None
    else:
        assert "uncalibrated" in result.stdout


def test_cli_ml_failures_and_clean_scan(tmp_path, artifact, monkeypatch):
    path, digest = artifact
    target = tmp_path / "input.txt"
    target.write_text("nothing here")
    runner = CliRunner()
    options = ["--model", str(path), "--model-sha256", digest]
    assert runner.invoke(app, ["scan", str(target), *options]).exit_code == 0
    for invalid in (
        ["--model", str(path)],
        ["--model-sha256", digest],
        ["--model", str(path), "--model-sha256", "0" * 64],
    ):
        result = runner.invoke(app, ["scan", str(target), *invalid])
        assert result.exit_code == 2
        assert "Traceback" not in result.output
    target.write_text("ghp_" + "Ab3x" * 9)

    def fail(*args):
        raise PredictionError("Safe error")

    monkeypatch.setattr(LocalPredictor, "score", fail)
    result = runner.invoke(app, ["scan", str(target), *options, "-f", "json"])
    assert result.exit_code == 2
    report = json.loads(result.stdout)
    assert report["complete"] is False
    assert len(report["findings"]) == 1
    assert report["findings"][0]["model_score"] is None


@pytest.mark.parametrize("mutation", ["missing", "threshold", "nan", "bool", "model", "classes"])
def test_artifact_prediction_schema_rejection(artifact, mutation):
    path, _ = artifact
    payload = pickle.loads(path.read_bytes())
    if mutation == "missing":
        del payload["threshold"]
    elif mutation == "threshold":
        payload["threshold"] = 2
    elif mutation == "nan":
        payload["threshold"] = float("nan")
    elif mutation == "bool":
        payload["threshold"] = True
    elif mutation == "model":
        payload["model"] = None
    else:
        payload["model"].classes_ = np.array([1, 0])
    data = pickle.dumps(payload)
    path.write_bytes(data)
    with pytest.raises(ValueError, match="prediction schema"):
        load_trusted_artifact(path, expected_sha256=hashlib.sha256(data).hexdigest())


def test_artifact_safe_deserialization_errors(tmp_path, artifact, monkeypatch):
    path, digest = artifact
    with pytest.raises(ValueError, match="read model"):
        load_trusted_artifact(tmp_path / "missing", expected_sha256=digest)
    for error in (ImportError("private input"), RuntimeError("private input")):

        def fail(data, error=error):
            raise error

        monkeypatch.setattr(pickle, "loads", fail)
        with pytest.raises(ValueError) as caught:
            load_trusted_artifact(path, expected_sha256=digest)
        assert "private input" not in str(caught.value)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="Named pipes require POSIX")
def test_model_named_pipe_is_rejected_without_blocking(tmp_path):
    path = tmp_path / "model.pipe"
    os.mkfifo(path)
    with pytest.raises(ValueError, match="regular file"):
        load_trusted_artifact(path, expected_sha256="0" * 64)


@pytest.mark.skipif(not hasattr(os, "O_NOFOLLOW"), reason="Requires O_NOFOLLOW")
def test_model_symlink_is_rejected(tmp_path, artifact):
    path, digest = artifact
    link = tmp_path / "link.pkl"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="read model"):
        load_trusted_artifact(link, expected_sha256=digest)


def test_html_escapes_all_dynamic_text():
    value = "ghp_" + "Ab3x" * 9
    injection = '<script>alert("x")</script>&'
    finding = replace(
        scan_text(value)[0],
        path=injection,
        explanation=injection,
        service=injection,
        rule_id=injection,
        severity=injection,
        masked_value=injection,
        model_decision=injection,
    )
    html = render_html(ScanReport(findings=[finding], errors=[injection]))

    class Tags(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tags = []

        def handle_starttag(self, tag, attrs):
            self.tags.append(tag)

    parser = Tags()
    parser.feed(html)
    assert "script" not in parser.tags
    assert injection not in html
    assert "&lt;script&gt;" in html
    assert "Content-Security-Policy" in html
    assert "Incomplete" in html
    assert "No candidates" in render_html(ScanReport())


def test_rules_mode_does_not_import_optional_ml_dependencies():
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import importlib.abc
import sys
class BlockML(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in {'sklearn', 'numpy', 'scipy'}:
            raise ImportError('Optional ML dependency requested')
sys.meta_path.insert(0, BlockML())
from secretsense.cli import app
from secretsense import scan_text
assert scan_text('nothing here') == []
""",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, "Rules mode imported an optional ML dependency."
