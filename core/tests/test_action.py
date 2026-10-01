"""Exercise the Action adapter locally without publishing or remote execution."""

import importlib.util
import json
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parents[2] / ".github" / "actions-runner" / "scan.py"
spec = importlib.util.spec_from_file_location("action_scan", RUNNER)
action = importlib.util.module_from_spec(spec)
spec.loader.exec_module(action)


@pytest.mark.parametrize("fail,expected", [("true", 1), ("false", 0)])
def test_action_findings_and_repository_relative_paths(
    tmp_path, monkeypatch, capsys, fail, expected
):
    workspace = tmp_path / "workspace"
    source = workspace / "src"
    source.mkdir(parents=True)
    value = "ghp_" + "Az39" * 9
    (source / "fixture.txt").write_text(value)
    output = tmp_path / "outputs"
    for name, setting in {
        "GITHUB_WORKSPACE": str(workspace),
        "RUNNER_TEMP": str(tmp_path),
        "GITHUB_OUTPUT": str(output),
        "INPUT_SCAN_PATH": "src",
        "INPUT_FAIL_ON_FINDINGS": fail,
    }.items():
        monkeypatch.setenv(name, setting)
    assert action.run() == expected
    outputs = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert outputs["exit-code"] == "1"
    report = Path(outputs["sarif"]).read_text()
    assert value not in report + capsys.readouterr().out
    physical = json.loads(report)["runs"][0]["results"][0]["locations"][0]["physicalLocation"]
    assert physical["artifactLocation"]["uri"] == "src/fixture.txt"


@pytest.mark.parametrize(
    "settings",
    [
        {"INPUT_HISTORY": "yes"},
        {"INPUT_SCAN_PATH": ".."},
        {"INPUT_SCAN_PATH": "$(touch marker)"},
        {"INPUT_HISTORY": "true"},
    ],
)
def test_action_errors_always_fail(tmp_path, monkeypatch, settings):
    for name, setting in {
        "GITHUB_WORKSPACE": str(tmp_path),
        "RUNNER_TEMP": str(tmp_path),
        "GITHUB_OUTPUT": str(tmp_path / "outputs"),
        "INPUT_FAIL_ON_FINDINGS": "false",
        **settings,
    }.items():
        monkeypatch.setenv(name, setting)
    assert action.run() == 2
    assert not (tmp_path / "marker").exists()


def test_action_output_error_is_safe(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
    monkeypatch.delenv("RUNNER_TEMP", raising=False)
    assert action.run() == 2
    assert "Unable to write" in capsys.readouterr().out
