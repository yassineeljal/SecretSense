"""Self-contained HTML with escaped data, no scripts, and no remote resources."""

from html import escape

from secretsense.scanner.engine import ScanReport


def render_html(report: ScanReport) -> str:
    rows = []
    for item in report.findings:
        fields = (
            f"{item.path}:{item.line}:{item.column}",
            item.service,
            item.rule_id,
            item.severity,
            item.masked_value,
            f"{item.model_score:.4f}" if item.model_score is not None else "Unscored",
            item.model_decision or "Unscored",
            item.explanation,
            item.commit or "Working tree",
            " ".join(item.remediation.steps) if item.remediation else "",
        )
        rows.append("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in fields) + "</tr>")
    errors = "".join(f"<li>{escape(error)}</li>" for error in report.errors)
    model_note = (
        f"Local ML threshold: {report.model['threshold']:g}. "
        "Scores are uncalibrated; all candidates are retained."
        if report.model
        else "Rules and entropy; ML scoring is disabled."
    )
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy"
 content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>SecretSense scan report</title>
<style>
body {{ font: 16px/1.5 system-ui, sans-serif; margin: 2rem; color: #172b3a; background: #fff; }}
h1 {{ margin-bottom: .25rem; }}
.table {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ text-align: left; border: 1px solid #ccd5dc; padding: .6rem; overflow-wrap: anywhere; }}
th {{ background: #eef3f6; }}
.errors {{ color: #992321; }}
</style></head>
<body><h1>SecretSense scan report</h1>
<p>Scan status: <strong>{"Complete" if report.complete else "Incomplete"}</strong>.
Scanned {report.files_scanned} file(s); skipped {report.entries_skipped} entries;
found {len(report.findings)} candidate(s).</p>
<p>{escape(model_note)} Scores and format matches do not establish credential validity.
A clean report is not a security guarantee.</p>
{'<h2>Processing errors</h2><ul class="errors">' + errors + "</ul>" if errors else ""}
<div class="table"><table><caption>Masked findings</caption>
<thead><tr><th scope="col">Location</th><th scope="col">Service</th><th scope="col">Rule</th>
<th scope="col">Severity</th><th scope="col">Masked value</th><th scope="col">ML score</th>
<th scope="col">ML decision</th><th scope="col">Explanation</th>
<th scope="col">Git snapshot</th><th scope="col">Remediation</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>
{"<p>No candidates found in the scanned files.</p>" if not rows else ""}
</body></html>"""
