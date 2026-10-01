"""Action entry point: inputs are data; no source commands or remote scanning."""

import os
import tempfile
from dataclasses import replace
from pathlib import Path

from secretsense.report.sarif import render_sarif
from secretsense.scanner.engine import ScanReport, scan_path
from secretsense.scanner.history import scan_history


def run() -> int:
    try:
        history = os.environ.get("INPUT_HISTORY", "false")
        fail = os.environ.get("INPUT_FAIL_ON_FINDINGS", "true")
        if history not in {"true", "false"} or fail not in {"true", "false"}:
            raise ValueError("Invalid boolean input.")
        workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
        target = workspace / os.environ.get("INPUT_SCAN_PATH", ".")
        if target.is_symlink():
            raise ValueError("Symlink target.")
        target = target.resolve()
        target.relative_to(workspace)
        limits = {
            "max_files": int(os.environ.get("INPUT_MAX_FILES", "10000")),
            "max_bytes": int(os.environ.get("INPUT_MAX_BYTES", "1048576")),
        }
        report = (
            scan_history(
                target,
                ref=os.environ.get("INPUT_REF", "HEAD"),
                **limits,
                max_commits=int(os.environ.get("INPUT_MAX_COMMITS", "100")),
                max_total_bytes=int(os.environ.get("INPUT_MAX_TOTAL_BYTES", "52428800")),
                timeout=float(os.environ.get("INPUT_TIMEOUT", "30")),
            )
            if history == "true"
            else scan_path(target, **limits)
        )
        base = target if target.is_dir() else target.parent
        prefix = base.relative_to(workspace)
        report.findings = [
            replace(item, path=(prefix / item.path).as_posix()) for item in report.findings
        ]
    except (OSError, ValueError, KeyError):
        report = ScanReport(errors=["Invalid Action input or inaccessible local scan target."])
        fail = "true"
    code = 2 if not report.complete else int(bool(report.findings))
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".sarif",
            prefix="secretsense-",
            dir=os.environ["RUNNER_TEMP"],
            delete=False,
            encoding="utf-8",
        ) as stream:
            stream.write(render_sarif(report))
            report_path = stream.name
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"sarif={report_path}\nexit-code={code}\n")
    except (OSError, KeyError):
        print("Unable to write the redacted Action report.")
        return 2
    print(f"SecretSense: {len(report.findings)} candidates; complete={report.complete}.")
    return code if code == 2 or fail == "true" else 0


if __name__ == "__main__":
    raise SystemExit(run())
