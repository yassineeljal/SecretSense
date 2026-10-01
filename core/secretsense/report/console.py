import json

from secretsense.scanner.engine import ScanReport


def render_console(report: ScanReport) -> str:
    lines = [
        f"Scanned {report.files_scanned} file(s); skipped {report.entries_skipped} entries; "
        f"found {len(report.findings)} candidate(s)."
    ]
    for finding in report.findings:
        # JSON quoting prevents filenames from injecting terminal control sequences.
        location = f"{json.dumps(finding.path, ensure_ascii=True)}:{finding.line}:{finding.column}"
        lines.append(
            f"{finding.severity.upper()} {location} {finding.rule_id} {finding.masked_value}"
        )
    lines.extend(f"ERROR: {error}" for error in report.errors)
    return "\n".join(lines)
