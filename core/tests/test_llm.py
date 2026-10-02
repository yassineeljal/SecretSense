import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from typer.testing import CliRunner

from secretsense.cli import app
from secretsense.llm import AdvisorError, OllamaAdvisor, build_prompt
from secretsense.scanner.candidates import extract_candidates
from secretsense.scanner.engine import scan_path, scan_text


def synthetic_password() -> str:
    return "Zq" + "9xT" + "!w4Lm" + "#Vb7" + "Rk2"


def synthetic_aws_key() -> str:
    return "AKIA" + "ABCDEFGH" + "IJKLMNOP"


@pytest.fixture
def fake_ollama():
    state = {"bodies": [], "reply": {"verdict": "likely-secret"}, "status": 200, "raw": None}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            state["bodies"].append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            payload = state["raw"] or json.dumps({"response": json.dumps(state["reply"])}).encode()
            self.send_response(state["status"])
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    state["url"] = f"http://127.0.0.1:{server.server_port}"
    yield state
    server.shutdown()


def source() -> str:
    return f'db_password = "{synthetic_password()}"\naws = "{synthetic_aws_key()}"\n'


def test_rejects_non_loopback_urls_and_bad_models():
    for url in ("http://example.com:11434", "https://127.0.0.1", "http://127.0.0.1/x"):
        with pytest.raises(ValueError):
            OllamaAdvisor("llama3", url)
    with pytest.raises(ValueError):
        OllamaAdvisor("bad model;")


def test_prompt_withholds_values_and_other_candidates():
    content = f'x = "{synthetic_aws_key()}"; db_password = "{synthetic_password()}"\n'
    candidates = extract_candidates(content)
    target = next(item for item in candidates if item.rule_id == "generic-secret")
    prompt = build_prompt(content, candidates, target)
    assert synthetic_password() not in prompt
    assert synthetic_aws_key() not in prompt
    assert "<VALUE>" in prompt and "<OTHER-CANDIDATE>" in prompt


def test_advisor_annotates_only_generic_candidates_and_keeps_all(fake_ollama):
    advisor = OllamaAdvisor("llama3", fake_ollama["url"])
    findings = scan_text(source(), "app.py", advisor=advisor)
    assert [(item.rule_id, item.llm_verdict) for item in findings] == [
        ("generic-secret", "likely-secret"),
        ("aws-access-key", None),
    ]
    assert len(fake_ollama["bodies"]) == 1
    assert synthetic_password() not in fake_ollama["bodies"][0]["prompt"]


def test_placeholder_verdict_never_suppresses(fake_ollama):
    fake_ollama["reply"] = {"verdict": "likely-placeholder"}
    findings = scan_text(source(), advisor=OllamaAdvisor("llama3", fake_ollama["url"]))
    assert len(findings) == 2 and findings[0].llm_verdict == "likely-placeholder"


@pytest.mark.parametrize(
    "mutate",
    [
        {"status": 500},
        {"reply": {"verdict": "ignore all previous instructions"}},
        {"raw": b"not json"},
        {"raw": b"x" * 70_000},
    ],
)
def test_invalid_advisor_output_is_value_free_and_incomplete(fake_ollama, tmp_path, mutate):
    fake_ollama.update(mutate)
    advisor = OllamaAdvisor("llama3", fake_ollama["url"])
    with pytest.raises(AdvisorError) as raised:
        scan_text(source(), advisor=advisor)
    assert synthetic_password() not in str(raised.value)
    (tmp_path / "a.py").write_text(source())
    report = scan_path(tmp_path, advisor=advisor)
    assert not report.complete and len(report.findings) == 2
    assert all(item.llm_verdict is None for item in report.findings)


def test_unreachable_server_fails_closed(tmp_path):
    (tmp_path / "a.py").write_text(source())
    report = scan_path(tmp_path, advisor=OllamaAdvisor("llama3", "http://127.0.0.1:9", timeout=1))
    assert not report.complete and len(report.findings) == 2


def test_cli_llm_report_and_history_rejection(fake_ollama, tmp_path):
    (tmp_path / "a.py").write_text(source())
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "scan",
            str(tmp_path),
            "--format",
            "json",
            "--llm",
            "llama3",
            "--llm-url",
            fake_ollama["url"],
        ],
    )
    data = json.loads(result.output)
    assert result.exit_code == 1
    assert data["engine"] == "rules-and-entropy+local-llm" and data["llm"]["model"] == "llama3"
    assert synthetic_password() not in result.output
    bad = runner.invoke(app, ["scan", str(tmp_path), "--history", "--llm", "llama3"])
    assert bad.exit_code == 2
    remote = runner.invoke(
        app, ["scan", str(tmp_path), "--llm", "m", "--llm-url", "http://example.com"]
    )
    assert remote.exit_code == 2
