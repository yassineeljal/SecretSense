import json

from typer.testing import CliRunner

from secretsense.cli import app

runner = CliRunner()


def test_help():
    assert runner.invoke(app, ["--help"]).exit_code == 0
    assert runner.invoke(app, ["scan", "--help"]).exit_code == 0


def test_clean_exit(tmp_path):
    (tmp_path / "clean.txt").write_text("nothing sensitive")
    result = runner.invoke(app, ["scan", str(tmp_path)])
    assert result.exit_code == 0
    assert "Scanned 1 file(s)" in result.stdout


def test_findings_json_and_exit_code(tmp_path):
    value = "AKIA" + "A1" * 8
    (tmp_path / "sample.txt").write_text(value)
    result = runner.invoke(app, ["scan", str(tmp_path), "--format", "json"])
    assert result.exit_code == 1
    assert value not in result.stdout
    assert json.loads(result.stdout)["findings"][0]["rule_id"] == "aws-access-key"


def test_incomplete_scan_exit(tmp_path):
    for name in ("a.txt", "b.txt"):
        (tmp_path / name).write_text("clean")
    result = runner.invoke(app, ["scan", str(tmp_path), "--max-files", "1", "-f", "json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["complete"] is False


def test_missing_target(tmp_path):
    result = runner.invoke(app, ["scan", str(tmp_path / "missing")])
    assert result.exit_code == 2
    assert "Traceback" not in result.output


def test_invalid_limit(tmp_path):
    assert runner.invoke(app, ["scan", str(tmp_path), "--max-bytes", "0"]).exit_code == 2
