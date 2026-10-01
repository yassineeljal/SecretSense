import json

from secretsense.scanner.engine import ScanReport


def render_console(report: ScanReport) -> str:
    lines = [
        f"Scanned {report.files_scanned} file(s); skipped {report.entries_skipped} entries; "
        f"found {len(report.findings)} candidate(s)."
    ]
    if report.model:
        lines.append(
            f"Local ML: uncalibrated scores; threshold {report.model['threshold']:g}; "
            "all candidates retained. Scores do not establish credential validity."
        )
    for finding in report.findings:
        # JSON quoting prevents filenames from injecting terminal control sequences.
        location = f"{json.dumps(finding.path, ensure_ascii=True)}:{finding.line}:{finding.column}"
        lines.append(
            f"{finding.severity.upper()} {location} {finding.rule_id} {finding.masked_value}"
            + (
                f" score={finding.model_score:.4f} {finding.model_decision}"
                if finding.model_score is not None
                else ""
            )
        )
        if finding.commit:
            lines.append(f"  Git snapshot: {finding.commit}")
        if finding.remediation:
            lines.extend(f"  {step}" for step in finding.remediation.steps)
    lines.extend(f"ERROR: {error}" for error in report.errors)
    return "\n".join(lines)
