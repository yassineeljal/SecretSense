"""Run from the checkout: uvicorn api.main:app --host 127.0.0.1 --no-access-log."""

import asyncio
import json
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse

from api.limits import Boundary, Limits
from api.schemas import ScanInput


async def _scan_in_worker(content: str, limits: Limits):
    # Shield process creation so cancellation cannot abandon an untracked child.
    startup = asyncio.create_task(
        asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "api.worker",
            cwd=Path(__file__).resolve().parent.parent,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
    )
    process = None
    try:
        process = await asyncio.shield(startup)
        payload = json.dumps({"content": content, "limit": limits.findings}, ensure_ascii=False)
        output, _ = await process.communicate(payload.encode())
        if process.returncode:
            raise RuntimeError
        result = json.loads(output)
        if "error" in result:
            return JSONResponse(
                {"detail": "Scan could not complete within resource limits."}, status_code=422
            )
        return JSONResponse(result)
    finally:
        if process is None:
            process = await startup
        if process.returncode is None:
            process.kill()
        await process.wait()


async def run_scan(content: str, limits: Limits):
    try:
        return await asyncio.wait_for(_scan_in_worker(content, limits), limits.scan_seconds)
    except TimeoutError:
        return JSONResponse(
            {"detail": "Scan deadline exceeded. No complete scan is available."}, 504
        )
    except (ValueError, RuntimeError, OSError):
        return JSONResponse({"detail": "Scan failed. No complete scan is available."}, 500)


def create_app(limits: Limits | None = None):
    limits = limits or Limits()
    application = FastAPI(
        title="SecretSense local API", docs_url=None, redoc_url=None, openapi_url=None
    )

    @application.exception_handler(RequestValidationError)
    @application.exception_handler(ValidationError)
    async def validation_error(request, exception):
        return JSONResponse({"detail": "Invalid scan request."}, 422)

    @application.exception_handler(HTTPException)
    async def http_error(request, exception):
        return JSONResponse({"detail": "Request is not supported."}, exception.status_code)

    @application.exception_handler(Exception)
    async def unexpected_error(request, exception):
        return JSONResponse({"detail": "Request failed."}, 500)

    @application.get("/api/health")
    async def health():
        return {"status": "ok", "mode": "local-demo"}

    @application.get("/api/model/info")
    async def model_info():
        return {
            "engine": "rules-and-entropy",
            "model": None,
            "scores_available": False,
            "policy": "retain-all-candidates",
            "limits": vars(limits),
        }

    @application.post("/api/scan")
    async def scan(request: Request):
        if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
            return JSONResponse({"detail": "Use an application/json request."}, 415)
        try:
            raw = await request.body()
            data = ScanInput.model_validate_json(raw)
            if "\x00" in data.content:
                return JSONResponse({"detail": "Only UTF-8 text is supported."}, 422)
            data.content.encode("utf-8")
        except (ValidationError, ValueError, UnicodeError):
            return JSONResponse({"detail": "Invalid scan request. Use nonempty UTF-8 text."}, 422)
        except ClientDisconnect:
            return JSONResponse({"detail": "Request disconnected."}, 400)
        return await run_scan(data.content, limits)

    application.add_middleware(Boundary, limits=limits)
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
        allow_methods=["POST", "GET"],
        allow_headers=["Content-Type"],
    )
    return application


app = create_app()
