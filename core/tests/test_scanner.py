"""Synthetic strings are assembled at runtime; no usable credentials are stored."""

import json
import math
import subprocess
import sys

import pytest

from secretsense import scan_path, scan_text
from secretsense.report.console import render_console
from secretsense.report.json_report import render_json
from secretsense.scanner.engine import ScanReport, mask_value
from secretsense.scanner.entropy import shannon_entropy

SAMPLES = [
    ("aws-access-key", "AKIA" + "A1" * 8),
    ("github-token", "ghp_" + "a1" * 18),
    ("gitlab-token", "glpat-" + "b2" * 10),
    ("stripe-key", "sk_test_" + "c3" * 12),
    ("slack-token", "xoxb-" + "1234567890-" * 3),
    ("google-api-key", "AIza" + "d4" * 17 + "x"),
    ("sendgrid-key", "SG." + "e5" * 11 + "." + "f6" * 21 + "x"),
    ("npm-token", "npm_" + "g7" * 18),
    ("pypi-token", "pypi-" + "h8" * 30),
    ("shopify-token", "shpat_" + "a9" * 16),
    ("digitalocean-token", "dop_v1_" + "ab" * 32),
    ("grafana-token", "glc_" + "i0" * 20),
    ("huggingface-token", "hf_" + "j1" * 17),
    ("docker-token", "dckr_pat_" + "k2" * 13 + "x"),
    ("mailgun-key", "key-" + "cd" * 16),
    ("jwt", "eyJ" + "a" * 12 + "." + "b" * 12 + "." + "c" * 12),
    ("private-key", "-----BEGIN " + "RSA PRIVATE KEY-----"),
]


@pytest.mark.parametrize(("rule_id", "value"), SAMPLES)
def test_patterns_locations_and_redaction(rule_id, value):
    findings = scan_text(f'# heading\nvalue = "{value}"\n', "config.py")
    assert len(findings) == 1
    finding = findings[0]
    assert (finding.rule_id, finding.line, finding.column) == (rule_id, 2, 10)
    report = ScanReport(findings=findings, files_scanned=1)
    for output in (render_console(report), render_json(report), repr(finding)):
        assert value not in output
    assert json.loads(render_json(report))["complete"] is True


def test_entropy_and_short_value_masking():
    assert shannon_entropy("") == 0
    assert shannon_entropy("aaaa") == 0
    assert math.isclose(shannon_entropy("abcd"), 2)
    assert mask_value("short") == "[REDACTED]"


def test_entropy_detects_assignment_but_not_arbitrary_hash():
    value = "aB3dE6gH9jK2mN5pQ8sT"
    findings = scan_text(f'password = "{value}"')
    assert [f.rule_id for f in findings] == ["generic-secret"]
    assert not scan_text(f'build_hash = "{value}"')


@pytest.mark.parametrize(
    "value",
    [
        "your_api_key_here",
        "changeme",
        "${MY_SECRET_VALUE}",
        "process.env.A_LONG_TOKEN_NAME",
        'os.getenv("MY_TOKEN")',
    ],
)
def test_placeholders_and_environment_lookups(value):
    assert not scan_text(f"api_key = {value}")


def test_no_duplicate_entropy_finding():
    value = "ghp_" + "aB3dE6gH9jK2mN5pQ8" * 2
    assert [f.rule_id for f in scan_text(f'token = "{value}"')] == ["github-token"]


def test_boundaries_reject_embedded_or_overlong_tokens():
    value = SAMPLES[0][1]
    assert not scan_text("prefix" + value)
    assert not scan_text(value + "A")


def test_multiple_matches_have_stable_positions():
    value = SAMPLES[0][1]
    findings = scan_text(f"{value}\n{value}")
    assert [(f.line, f.column) for f in findings] == [(1, 1), (2, 1)]


def test_unsafe_filename_is_escaped():
    report = ScanReport(findings=scan_text(SAMPLES[0][1], "unsafe\x1b[31m\nname"))
    assert "\x1b" not in render_console(report)
    assert "unsafe\\u001b[31m\\nname" in render_console(report)


def test_missing_target_and_invalid_limits(tmp_path):
    with pytest.raises(ValueError):
        scan_path(tmp_path / "missing")
    with pytest.raises(ValueError):
        scan_path(tmp_path, max_files=0)


def test_long_nonsecret_input_finishes_within_subprocess_deadline():
    # Repeated word boundaries must not trigger quadratic assignment matching.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            ("from secretsense import scan_text; assert not scan_text('ordinary.' * 12000)"),
        ],
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode()
