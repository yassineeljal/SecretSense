"""Bounded admission and streaming input before request parsing."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass

from starlette.responses import JSONResponse


@dataclass(frozen=True)
class Limits:
    body_bytes: int = 1_048_576
    concurrency: int = 2
    requests_per_minute: int = 30
    request_seconds: float = 10
    scan_seconds: float = 5
    findings: int = 1000


class RequestTooLarge(Exception):
    pass


class Boundary:
    """Single-process limits, including slow uploads; never queue scan requests."""

    def __init__(self, app, limits: Limits):
        self.app = app
        self.limits = limits
        self.active = 0
        self.arrivals = deque()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def secure_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + [
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                ]
            await send(message)

        async def reject(status, detail):
            headers = {"Retry-After": "60"} if status in (429, 503) else None
            await JSONResponse({"detail": detail}, status, headers=headers)(
                scope, receive, secure_send
            )

        headers = dict(scope.get("headers", []))
        origin = headers.get(b"origin")
        if origin and origin not in (b"http://127.0.0.1:3000", b"http://localhost:3000"):
            return await reject(403, "Origin is not allowed.")
        if scope["method"] != "POST":
            return await self.app(scope, receive, secure_send)
        now = time.monotonic()
        while self.arrivals and now - self.arrivals[0] >= 60:
            self.arrivals.popleft()
        if len(self.arrivals) >= self.limits.requests_per_minute:
            return await reject(429, "Request rate limit reached. Try again later.")
        self.arrivals.append(now)
        if self.active >= self.limits.concurrency:
            return await reject(503, "Scanner is busy. Try again later.")
        if headers.get(b"content-encoding", b"identity") != b"identity":
            return await reject(415, "Compressed requests are not supported.")
        length = headers.get(b"content-length")
        if length is not None:
            try:
                if int(length) < 0:
                    raise ValueError
                if int(length) > self.limits.body_bytes:
                    return await reject(413, "Request exceeds the byte limit.")
            except ValueError:
                return await reject(400, "Invalid request length.")
        received = 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > self.limits.body_bytes:
                raise RequestTooLarge
            return message

        self.active += 1
        try:
            await asyncio.wait_for(
                self.app(scope, bounded_receive, secure_send), self.limits.request_seconds
            )
        except RequestTooLarge:
            await reject(413, "Request exceeds the byte limit.")
        except TimeoutError:
            await reject(504, "Request deadline exceeded. No complete scan is available.")
        except Exception:
            await reject(500, "Request failed. No complete scan is available.")
        finally:
            self.active -= 1
