"""SARIF 2.1.0 with metadata-only locations and no embedded source content."""

import hashlib
import json
from urllib.parse import quote

from secretsense.scanner.engine import ScanReport


def render_sarif(report: ScanReport) -> str:
    rules = {}
    results = []
    for item in report.findings:
        rules.setdefault(
            item.rule_id,
            {
                "id": item.rule_id,
                "shortDescription": {"text": f"Potential {item.service} credential"},
                "help": {
                    "text": "\n".join(item.remediation.steps)
                    if item.remediation
                    else item.explanation
                },
            },
        )
        # Metadata only: do not hash secret bytes or source lines into public reports.
        identity = json.dumps([item.path, item.rule_id, item.line, item.column, item.commit])
        result = {
            "ruleId": item.rule_id,
            "level": "error" if item.severity in {"critical", "high"} else "warning",
            "message": {"text": item.explanation + " Potential credential: [REDACTED]."},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": quote(item.path, safe="/")},
                        "region": {"startLine": item.line, "startColumn": item.column},
                    }
                }
            ],
            "partialFingerprints": {
                "primaryLocationLineHash": hashlib.sha256(identity.encode()).hexdigest()
            },
            "properties": {
                "service": item.service,
                "severity": item.severity,
                "modelScore": item.model_score,
                "modelDecision": item.model_decision,
                "commit": item.commit,
                "blob": item.blob,
            },
        }
        results.append(result)
    return json.dumps(
        {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "SecretSense",
                            "version": "0.1.0",
                            "rules": list(rules.values()),
                        }
                    },
                    "columnKind": "unicodeCodePoints",
                    "results": results,
                    "invocations": [
                        {
                            "executionSuccessful": report.complete,
                            "toolExecutionNotifications": [
                                {"level": "error", "message": {"text": error}}
                                for error in report.errors
                            ],
                        }
                    ],
                    "properties": {
                        "engine": report.engine,
                        "model": report.model,
                        "history": report.history,
                        "filesScanned": report.files_scanned,
                        "entriesSkipped": report.entries_skipped,
                    },
                }
            ],
        },
        indent=2,
        ensure_ascii=True,
    )
