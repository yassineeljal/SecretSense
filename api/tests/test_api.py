"""Boundary tests construct synthetic values only at runtime."""

import asyncio
import json
import sys
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient

from api.limits import Boundary, Limits
from api.main import create_app, run_scan


def client(limits=None):
    return TestClient(create_app(limits), base_url="http://127.0.0.1")


def token():
    return "gh" + "p_" + "aB3cD4eF5" * 4


def test_scan_redacts_values_source_and_filename(caplog):
    value = token()
    response = client().post(
        "/api/scan",
        json={
            "content": f'// private context\naccess_token = "{value}"',
            "filename": value,
        },
    )
    assert response.status_code == 200
    report = response.json()
    assert report["complete"] and report["files_scanned"] == 1
    finding = report["findings"][0]
    assert finding["line"] == 2 and finding["service"] == "GitHub"
    assert finding["masked_value"] == "[REDACTED]"
    assert finding["path"] == "submitted.txt" and finding["remediation"]["steps"]
    assert finding["model_score"] is None
    for forbidden in (value, "private context", "access_token"):
        assert forbidden not in response.text + caplog.text
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"content": ""},
        {"content": 1},
        {"content": "ok", "extra": "private"},
        {"content": "\x00"},
        {"content": "\ud800"},
        {"content": "ok", "filename": "x" * 256},
    ],
)
def test_invalid_input_has_generic_errors(payload):
    response = client().post(
        "/api/scan", content=json.dumps(payload), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    assert "input" not in response.json() and "private" not in response.text


def test_clean_health_info_and_unsupported_routes():
    with client() as session:
        assert session.get("/api/health").json()["status"] == "ok"
        assert session.get("/api/model/info").json()["model"] is None
        assert session.post("/api/scan", json={"content": "print(42)"}).json()["findings"] == []
        assert (
            session.post("/api/scan/repo", json={"url": "https://example.org"}).status_code == 404
        )
        assert session.post("/api/scan", content="private").status_code == 415
        response = session.post(
            "/api/scan", content=b'{"content":', headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422 and "content" not in response.text


def test_size_rate_compression_origin_and_host():
    with client(Limits(body_bytes=64, requests_per_minute=2)) as session:
        assert session.post("/api/scan", json={"content": "x" * 65}).status_code == 413
        assert session.post("/api/scan", headers={"Content-Encoding": "gzip"}).status_code == 415
        response = session.post("/api/scan", json={"content": "ok"})
        assert response.status_code == 429 and response.headers["retry-after"] == "60"
        assert session.get("/api/health").status_code == 200
    with client() as session:
        assert (
            session.post("/api/scan", headers={"Origin": "https://hostile.example"}).status_code
            == 403
        )
        assert session.get("/api/health", headers={"Host": "hostile.example"}).status_code == 400
        response = session.options(
            "/api/scan",
            headers={"Origin": "http://127.0.0.1:3000", "Access-Control-Request-Method": "POST"},
        )
        assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_chunked_body_deadline_concurrency_and_release():
    async def check():
        limits = Limits(body_bytes=40, concurrency=1, request_seconds=0.05)
        app = create_app(limits)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1"
        ) as session:

            async def oversized():
                yield b'{"content":"'
                yield b"x" * 41

            response = await session.post(
                "/api/scan", content=oversized(), headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 413
            entered = asyncio.Event()

            async def slow():
                entered.set()
                await asyncio.sleep(1)
                yield b"{}"

            task = asyncio.create_task(
                session.post(
                    "/api/scan", content=slow(), headers={"Content-Type": "application/json"}
                )
            )
            await entered.wait()
            assert (await session.post("/api/scan", json={"content": "ok"})).status_code == 503
            assert (await task).status_code == 504
            assert (await session.post("/api/scan", json={})).status_code == 422

    asyncio.run(check())


def test_finding_limit_never_reports_partial_success():
    response = client(Limits(findings=1)).post(
        "/api/scan", json={"content": token() + "\n" + token()}
    )
    assert response.status_code == 422 and "findings" not in response.json()


def test_worker_timeout_and_cancellation_reap_child(monkeypatch):
    async def check(cancel):
        original = asyncio.create_subprocess_exec
        children = []

        async def slow_worker(*args, **kwargs):
            process = await original(sys.executable, "-c", "import time; time.sleep(30)", **kwargs)
            children.append(process)
            return process

        monkeypatch.setattr(asyncio, "create_subprocess_exec", slow_worker)
        task = asyncio.create_task(run_scan("ok", Limits(scan_seconds=0.05 if not cancel else 5)))
        if cancel:
            while not children:
                await asyncio.sleep(0.005)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        else:
            assert (await task).status_code == 504
        assert children[0].returncode is not None
        monkeypatch.setattr(asyncio, "create_subprocess_exec", original)

    asyncio.run(check(False))
    asyncio.run(check(True))


def test_boundary_rate_expires_and_does_not_trust_forwarded_ip(monkeypatch):
    async def check():
        async def app(scope, receive, send):
            from starlette.responses import JSONResponse

            await JSONResponse({})(scope, receive, send)

        boundary = Boundary(app, replace(Limits(), requests_per_minute=1))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=boundary), base_url="http://127.0.0.1"
        ) as session:
            assert (
                await session.post("/", headers={"X-Forwarded-For": "1.2.3.4"})
            ).status_code == 200
            assert (
                await session.post("/", headers={"X-Forwarded-For": "2.3.4.5"})
            ).status_code == 429
            boundary.arrivals[0] -= 61
            assert (await session.post("/")).status_code == 200

    asyncio.run(check())


def test_unexpected_failures_never_escape_to_logs(monkeypatch, caplog):
    async def fail(*args):
        raise RuntimeError(token())

    monkeypatch.setattr("api.main.run_scan", fail)
    response = client().post("/api/scan", json={"content": "ok"})
    assert response.status_code == 500
    assert token() not in response.text + caplog.text
    assert response.headers["cache-control"] == "no-store"


def test_worker_output_and_generic_failures(monkeypatch):
    import io
    from types import SimpleNamespace

    from api import worker

    for raw, expected in [
        (json.dumps({"content": token(), "limit": 10}).encode(), "findings"),
        (b"invalid", "error"),
        (json.dumps({"content": token(), "limit": 0}).encode(), "error"),
    ]:
        output = io.BytesIO()
        monkeypatch.setattr(worker.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(raw)))
        monkeypatch.setattr(worker.sys, "stdout", SimpleNamespace(buffer=output))
        worker.main()
        encoded = output.getvalue()
        assert expected in json.loads(encoded)
        assert token().encode() not in encoded


def test_length_header_rejection():
    for length, status in [("-1", 400), ("invalid", 400), ("2000000", 413)]:
        response = client().post("/api/scan", headers={"Content-Length": length})
        assert response.status_code == status


def test_boundary_does_not_execute_input(tmp_path):
    marker = tmp_path / "must-not-exist"
    content = f"from pathlib import Path\nPath({str(marker)!r}).touch()"
    assert client().post("/api/scan", json={"content": content}).status_code == 200
    assert not marker.exists()


def test_cancel_during_worker_startup_reaps_child(monkeypatch):
    async def check():
        original = asyncio.create_subprocess_exec
        started = asyncio.Event()
        children = []

        async def delayed_start(*args, **kwargs):
            process = await original(sys.executable, "-c", "import time; time.sleep(30)", **kwargs)
            children.append(process)
            started.set()
            await asyncio.sleep(0.05)
            return process

        monkeypatch.setattr(asyncio, "create_subprocess_exec", delayed_start)
        task = asyncio.create_task(run_scan("ok", Limits()))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert children[0].returncode is not None

    asyncio.run(check())
