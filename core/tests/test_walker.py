import os
from pathlib import Path

import pytest

from secretsense import scan_path
from secretsense.scanner import engine


def write_candidate(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("AKIA" + "A1" * 8)


def test_nested_ignores_negation_and_anchoring(tmp_path):
    (tmp_path / ".gitignore").write_text("*.secret\n/root-only.txt\nblocked/\n")
    write_candidate(tmp_path / "ignored.secret")
    write_candidate(tmp_path / "root-only.txt")
    write_candidate(tmp_path / "blocked" / "hidden.txt")
    (tmp_path / "blocked" / ".gitignore").write_text("!hidden.txt\n")
    write_candidate(tmp_path / "nested" / "keep.secret")
    write_candidate(tmp_path / "nested" / "ignore.secret")
    write_candidate(tmp_path / "nested" / "root-only.txt")
    (tmp_path / "nested" / ".gitignore").write_text("!keep.secret\n")
    report = scan_path(tmp_path)
    assert report.complete
    assert [f.path for f in report.findings] == ["nested/keep.secret", "nested/root-only.txt"]


def test_default_exclusions_binary_encoding_size_and_symlinks(tmp_path):
    write_candidate(tmp_path / "ok.txt")
    for directory in (".git", "node_modules", ".venv", "build"):
        write_candidate(tmp_path / directory / "hidden.txt")
    (tmp_path / "binary.dat").write_bytes(b"\x00" + b"AKIA" + b"A1" * 8)
    (tmp_path / "encoding.dat").write_bytes(b"\xff")
    (tmp_path / "large.txt").write_text("x" * 101)
    (tmp_path / "link.txt").symlink_to(tmp_path / "ok.txt")
    (tmp_path / "loop").symlink_to(tmp_path, target_is_directory=True)
    report = scan_path(tmp_path, max_bytes=100)
    assert report.complete
    assert report.files_scanned == 1
    assert len(report.findings) == 1
    assert report.entries_skipped == 9


def test_explicit_file_can_be_scanned_even_if_ignored(tmp_path):
    (tmp_path / ".gitignore").write_text(".env\n")
    write_candidate(tmp_path / ".env")
    assert not scan_path(tmp_path).findings
    assert scan_path(tmp_path / ".env").findings


def test_symlink_target_rejected(tmp_path):
    write_candidate(tmp_path / "real.txt")
    link = tmp_path / "link.txt"
    link.symlink_to(tmp_path / "real.txt")
    with pytest.raises(ValueError, match="symbolic link"):
        scan_path(link)


def test_entry_limit_marks_partial_scan(tmp_path):
    write_candidate(tmp_path / "a.txt")
    write_candidate(tmp_path / "b.txt")
    report = scan_path(tmp_path, max_files=1)
    assert not report.complete
    assert report.files_scanned == 1


def test_nested_entry_limit_does_not_silently_skip_siblings(tmp_path):
    write_candidate(tmp_path / "nested" / "a.txt")
    write_candidate(tmp_path / "other.txt")
    assert not scan_path(tmp_path, max_files=2).complete


def test_unreadable_file_marks_partial_scan_without_leaking_error(tmp_path, monkeypatch):
    write_candidate(tmp_path / "a.txt")

    def denied(*args):
        raise PermissionError("sensitive exception details")

    monkeypatch.setattr(engine, "read_text", denied)
    report = scan_path(tmp_path)
    assert not report.complete
    assert "sensitive" not in repr(report)


def test_invalid_ignore_file_marks_scan_incomplete(tmp_path):
    (tmp_path / ".gitignore").write_bytes(b"\xff")
    assert not scan_path(tmp_path).complete


def test_oversized_ignore_file_marks_scan_incomplete(tmp_path):
    (tmp_path / ".gitignore").write_bytes(b"x" * 1_048_577)
    report = scan_path(tmp_path)
    assert not report.complete
    assert "configuration limit" in report.errors[0]


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="Requires Unix named pipes")
def test_named_pipe_is_skipped(tmp_path):
    os.mkfifo(tmp_path / "pipe")
    report = scan_path(tmp_path)
    assert report.entries_skipped == 1
    assert report.complete
