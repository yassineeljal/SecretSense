"""Report contracts, actionable coverage, and value-free SARIF."""

import json
from dataclasses import replace
from urllib.parse import unquote

from secretsense.remediation import ACTIONS, get_playbook
from secretsense.report.sarif import render_sarif
from secretsense.scanner.engine import ScanReport, scan_text
from secretsense.scanner.patterns import RULES


def test_playbook_coverage_and_jwt_distinction():
    assert {rule.service for rule in RULES} <= ACTIONS.keys()
    assert "credential owner" in get_playbook("Generic").steps[1]
    assert "only if" in get_playbook("JWT").steps[1]


def test_sarif_contract_privacy_locations_and_stability():
    value = "ghp_" + "Az39" * 9
    finding = scan_text("\n" + value, "dir/a #?.py")[0]
    report = ScanReport(findings=[finding, replace(finding, line=3)])
    rendered = render_sarif(report)
    data = json.loads(rendered)
    assert data["version"] == "2.1.0"
    run = data["runs"][0]
    assert len(run["tool"]["driver"]["rules"]) == 1
    results = run["results"]
    physical = results[0]["locations"][0]["physicalLocation"]
    assert unquote(physical["artifactLocation"]["uri"]) == finding.path
    assert physical["region"] == {"startLine": 2, "startColumn": 1}
    assert results[0]["partialFingerprints"] != results[1]["partialFingerprints"]
    assert render_sarif(report) == rendered
    assert value not in rendered and "snippet" not in rendered
    assert "[REDACTED]" in rendered
    assert run["invocations"][0]["executionSuccessful"]
    assert finding.remediation is not None
    assert json.loads(json.dumps(report.to_dict()))["findings"][0]["remediation"]["steps"]


def test_sarif_clean_and_incomplete():
    report = json.loads(render_sarif(ScanReport(errors=["Safe failure"])))
    run = report["runs"][0]
    assert run["results"] == []
    assert not run["invocations"][0]["executionSuccessful"]
    assert (
        run["invocations"][0]["toolExecutionNotifications"][0]["message"]["text"] == "Safe failure"
    )
