"""Local synthetic Git histories, bounds, privacy, and unsafe configuration."""

import json
import os
import subprocess
import time
from dataclasses import dataclass, field

import pytest
from typer.testing import CliRunner

from secretsense.cli import app
from secretsense.model.predict import PredictionError
from secretsense.scanner.history import GitReadError, LocalGit, scan_history


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)
    return result.stdout.decode().strip()


@dataclass
class SyntheticRepository:
    root: object
    value: str = field(repr=False)
    first: str

    def __iter__(self):
        return iter((self.root, self.value, self.first))

    def __getitem__(self, index):
        return (self.root, self.value, self.first)[index]


@pytest.fixture
def repository(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Synthetic test")
    value = "ghp_" + "Az39" * 9
    (tmp_path / "removed.txt").write_text(value)
    (tmp_path / "odd #\nname.txt").write_text(value)
    (tmp_path / ".gitignore").write_text("removed.txt\n")
    git(tmp_path, "add", "-f", ".")
    git(tmp_path, "commit", "-qm", "Synthetic first snapshot")
    first = git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "removed.txt").unlink()
    (tmp_path / "clean.txt").write_text("nothing here")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "Remove synthetic value")
    return SyntheticRepository(tmp_path, value, first)


def test_deleted_files_dedup_and_provenance(repository):
    root, value, first = repository
    report = scan_history(root)
    assert report.complete
    assert len(report.findings) == 2
    assert report.history["commits_scanned"] == 2
    item = next(item for item in report.findings if item.path == "removed.txt")
    assert item.commit == first
    assert len(item.blob) == 40
    assert value not in repr(report)
    assert value not in json.dumps(report.to_dict())
    assert (root / "clean.txt").read_text() == "nothing here"
    assert not (root / "removed.txt").exists()


@pytest.mark.parametrize(
    "options,reason",
    [
        ({"max_commits": 1}, "commit limit"),
        ({"max_files": 1}, "entry limit"),
        ({"max_bytes": 1}, "blob size limit"),
        ({"max_total_bytes": 1}, "total byte limit"),
        ({"timeout": 0.000001}, "deadline"),
    ],
)
def test_history_bounds_are_incomplete(repository, options, reason):
    report = scan_history(repository[0], **options)
    assert not report.complete
    assert any(reason in error for error in report.errors)


def test_invalid_targets_refs_and_limits(repository, tmp_path):
    root, value, _ = repository
    for ref in ("--all", value, "HEAD~999"):
        report = scan_history(root, ref=ref)
        assert not report.complete and value not in repr(report)
    with pytest.raises(ValueError):
        scan_history(root, max_commits=0)
    with pytest.raises(ValueError):
        scan_history(root / "absent")
    nested = root / "nested"
    nested.mkdir()
    assert not scan_history(nested).complete
    empty = tmp_path / "not-a-repo"
    empty.mkdir()
    assert not scan_history(empty).complete


def test_ignored_environment_filters_and_symlinks(repository, monkeypatch):
    root, value, _ = repository
    marker = root / "executed"
    git(root, "config", "filter.evil.smudge", f"touch {marker}")
    git(root, "config", "diff.evil.textconv", f"touch {marker}")
    (root / ".gitattributes").write_text("* filter=evil diff=evil\n")
    (root / "link").symlink_to(root / "odd #\nname.txt")
    git(root, "add", ".gitattributes", "link")
    git(root, "commit", "-qm", "Add untrusted attributes")
    monkeypatch.setenv("GIT_DIR", str(root / "missing"))
    monkeypatch.setenv("GIT_TRACE", str(marker))
    report = scan_history(root)
    assert report.complete and len(report.findings) == 2
    assert report.entries_skipped >= 1
    assert not marker.exists()
    assert all(item.path != "link" for item in report.findings)


def test_shallow_history(repository, tmp_path):
    clone = tmp_path / "clone"
    git(repository[0], "clone", "-q", "--depth=1", repository[0].as_uri(), str(clone))
    report = scan_history(clone)
    assert not report.complete and "Shallow" in report.errors[0]


def test_safe_git_output_limit_and_failures(repository, monkeypatch):
    root, value, _ = repository
    reader = LocalGit(root, time.monotonic() + 5)
    with pytest.raises(GitReadError, match="output limit"):
        reader.read("rev-parse", "HEAD", limit=1)
    monkeypatch.setenv("PATH", "/nonexistent")
    with pytest.raises(GitReadError, match="Unable to run"):
        reader.read("rev-parse", "HEAD")


def test_history_prediction_failure_and_cli(repository):
    class Predictor:
        sha256 = "a" * 64
        threshold = 0.5

        def score(self, *args):
            raise PredictionError("Safe error")

    root, value, _ = repository
    report = scan_history(root, predictor=Predictor())
    assert not report.complete and len(report.findings) == 2
    assert all(item.model_score is None for item in report.findings)
    for format in ("json", "sarif", "html", "console"):
        result = CliRunner().invoke(app, ["scan", str(root), "--history", "-f", format])
        assert result.exit_code == 1
        assert value not in result.stdout
    result = CliRunner().invoke(app, ["scan", str(root), "--history", "--max-commits", "1"])
    assert result.exit_code == 2


def test_binary_and_non_utf8_skipped(repository):
    root = repository[0]
    (root / "binary").write_bytes(b"\0binary")
    (root / "invalid").write_bytes(b"\xff")
    git(root, "add", "binary", "invalid")
    git(root, "commit", "-qm", "Non-text fixtures")
    report = scan_history(root)
    assert report.complete
    assert report.entries_skipped == 2


def test_timeout_kills_git_process(tmp_path, monkeypatch):
    executable = tmp_path / "git"
    executable.write_text("#!/usr/bin/env python3\nimport time\ntime.sleep(10)\n")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    reader = LocalGit(tmp_path, time.monotonic() + 0.1)
    with pytest.raises(GitReadError, match="deadline"):
        reader.read("rev-parse", "HEAD")


def test_missing_promisor_blob_never_runs_remote_helper(repository):
    root, value, _ = repository
    oid = git(root, "rev-parse", "HEAD:odd #\nname.txt")
    (root / ".git" / "objects" / oid[:2] / oid[2:]).unlink()
    marker = root / "remote-executed"
    git(root, "config", "core.repositoryformatversion", "1")
    git(root, "config", "extensions.partialClone", "origin")
    git(root, "config", "remote.origin.promisor", "true")
    git(root, "config", "remote.origin.url", f"ext::touch {marker}")
    git(root, "config", "protocol.ext.allow", "always")
    report = scan_history(root)
    assert not report.complete
    assert not marker.exists()
    assert value not in repr(report)


def test_bare_repository_and_non_utf8_path(repository, tmp_path):
    bare = tmp_path / "bare.git"
    git(repository[0], "clone", "-q", "--bare", str(repository[0]), str(bare))
    report = scan_history(bare)
    assert report.complete and len(report.findings) == 2
    # Store the path in a Git tree directly: macOS filesystems reject these bytes.
    blob = git(repository[0], "rev-parse", "HEAD:clean.txt").encode()
    tree = (
        subprocess.run(
            ["git", "-C", str(repository[0]), "mktree", "-z"],
            input=b"100644 blob " + blob + b"\tbad-\xff.txt\0",
            capture_output=True,
            check=True,
        )
        .stdout.decode()
        .strip()
    )
    commit = git(repository[0], "commit-tree", tree, "-p", "HEAD", "-m", "Non-UTF-8 path")
    git(repository[0], "update-ref", "HEAD", commit)
    report = scan_history(repository[0])
    assert not report.complete
    assert any("path is not UTF-8" in error for error in report.errors)


@pytest.mark.parametrize("timeout", [float("nan"), float("inf"), 0])
def test_non_finite_deadlines_are_invalid(repository, timeout):
    with pytest.raises(ValueError):
        scan_history(repository[0], timeout=timeout)
