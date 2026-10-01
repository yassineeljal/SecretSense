"""Bounded local Git snapshots, without checkout, filters, hooks, or network fetches."""

import math
import os
import re
import subprocess
import threading
import time
from dataclasses import replace
from pathlib import Path

from secretsense.model.predict import LocalPredictor, PredictionError
from secretsense.scanner.engine import ScanReport, new_report, scan_text


class GitReadError(Exception):
    """Value-free Git failure, including deadline and output limits."""


class LocalGit:
    def __init__(self, root: Path, deadline: float):
        self.root = root
        self.deadline = deadline

    def read(self, *arguments: str, limit: int = 4096) -> bytes:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise GitReadError("Git history deadline reached; the scan is incomplete.")
        # Drop inherited Git configuration, alternate object paths and tracing.
        env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT") if key in os.environ}
        env.update(
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_TERMINAL_PROMPT="0",
            GIT_NO_LAZY_FETCH="1",
            GIT_ALLOW_PROTOCOL="",
            GIT_PROTOCOL_FROM_USER="0",
            GIT_OPTIONAL_LOCKS="0",
        )
        command = [
            "git",
            "--no-replace-objects",
            "-c",
            "protocol.allow=never",
            "-c",
            "core.hooksPath=" + os.devnull,
            "-c",
            "core.fsmonitor=false",
            "-C",
            str(self.root),
            *arguments,
        ]
        data = bytearray()
        try:
            with subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env
            ) as process:

                def read_output():
                    while chunk := process.stdout.read(min(65536, limit + 1 - len(data))):
                        data.extend(chunk)
                        if len(data) > limit:
                            process.kill()
                            return

                reader = threading.Thread(target=read_output, daemon=True)
                reader.start()
                try:
                    process.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    raise GitReadError(
                        "Git history deadline reached; the scan is incomplete."
                    ) from None
                finally:
                    reader.join()
                if len(data) > limit:
                    raise GitReadError("Git output limit reached; the scan is incomplete.")
                if process.returncode:
                    raise GitReadError("Unable to read local Git objects; the scan is incomplete.")
        except OSError:
            raise GitReadError("Unable to run local Git; the scan is incomplete.") from None
        return bytes(data)


def scan_history(
    path: str | Path,
    *,
    ref: str = "HEAD",
    max_commits: int = 100,
    max_bytes: int = 1_048_576,
    max_files: int = 10_000,
    max_total_bytes: int = 52_428_800,
    timeout: float = 30,
    predictor: LocalPredictor | None = None,
) -> ScanReport:
    """Scan unique (path, blob) pairs reachable from one local commit, newest first.

    Findings record the first encountered snapshot, not the introducing commit.
    Ignore files do not hide tracked history. Symlinks/submodules are never followed.
    """
    if (
        not math.isfinite(timeout)
        or min(max_commits, max_bytes, max_files, max_total_bytes, timeout) <= 0
    ):
        raise ValueError("History scan limits must be positive.")
    root = Path(path).absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("History scanning requires a local repository directory.")
    report = new_report(predictor)
    report.history = {
        "commits_scanned": 0,
        "entries_visited": 0,
        "bytes_scanned": 0,
        "scope": "unique-path-blob-snapshots",
        "resolved_commit": None,
    }
    git = LocalGit(root, time.monotonic() + timeout)
    seen = set()
    try:
        # Prevent Git from discovering a repository outside the supplied target.
        git.read("rev-parse", "--git-dir")
        prefix = git.read("rev-parse", "--show-prefix").strip()
        if prefix:
            raise GitReadError("History scanning requires the repository root.")
        commit = git.read("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").strip()
        if not re.fullmatch(rb"[a-f0-9]{40}|[a-f0-9]{64}", commit):
            raise GitReadError("Unable to resolve the local Git revision.")
        report.history["resolved_commit"] = commit.decode("ascii")
        if git.read("rev-parse", "--is-shallow-repository").strip() == b"true":
            report.errors.append("Shallow Git history; earlier commits are unavailable.")
        commits = git.read(
            "rev-list",
            f"--max-count={max_commits + 1}",
            commit.decode(),
            limit=(max_commits + 1) * 66,
        ).splitlines()
        if len(commits) > max_commits:
            report.errors.append("Git commit limit reached; the scan is incomplete.")
        for revision in commits[:max_commits]:
            entries = git.read(
                "ls-tree", "-r", "-z", "--full-tree", revision.decode(), limit=8_388_608
            ).split(b"\0")
            for entry in filter(None, entries):
                if report.history["entries_visited"] >= max_files:
                    raise GitReadError("Git entry limit reached; the scan is incomplete.")
                report.history["entries_visited"] += 1
                metadata, raw_path = entry.split(b"\t", 1)
                mode, kind, oid = metadata.split()
                if mode not in (b"100644", b"100755") or kind != b"blob":
                    report.entries_skipped += 1
                    continue
                pair = (raw_path, oid)
                if pair in seen:
                    continue
                seen.add(pair)
                try:
                    filename = raw_path.decode("utf-8")
                except UnicodeDecodeError:
                    report.entries_skipped += 1
                    report.errors.append("A Git path is not UTF-8; the scan is incomplete.")
                    continue
                size = int(git.read("cat-file", "-s", oid.decode()).strip())
                if size > max_bytes:
                    report.entries_skipped += 1
                    report.errors.append("Git blob size limit reached; the scan is incomplete.")
                    continue
                if report.history["bytes_scanned"] + size > max_total_bytes:
                    raise GitReadError("Git total byte limit reached; the scan is incomplete.")
                raw = git.read("cat-file", "blob", oid.decode(), limit=max_bytes)
                report.history["bytes_scanned"] += len(raw)
                try:
                    content = raw.decode("utf-8-sig") if b"\0" not in raw else None
                except UnicodeDecodeError:
                    content = None
                if content is None:
                    report.entries_skipped += 1
                    continue
                try:
                    findings = scan_text(content, filename, predictor=predictor)
                except PredictionError:
                    report.errors.append(
                        "Local model prediction failed; some findings remain unscored."
                    )
                    findings = scan_text(content, filename)
                report.findings.extend(
                    replace(item, commit=revision.decode(), blob=oid.decode()) for item in findings
                )
                report.files_scanned += 1
                if time.monotonic() >= git.deadline:
                    raise GitReadError("Git history deadline reached; the scan is incomplete.")
            report.history["commits_scanned"] += 1
    except (GitReadError, ValueError) as error:
        # Parsing errors can contain raw Git metadata; never forward their text.
        report.errors.append(
            str(error)
            if isinstance(error, GitReadError)
            else "Invalid local Git metadata; the scan is incomplete."
        )
    report.errors = list(dict.fromkeys(report.errors))
    return report
