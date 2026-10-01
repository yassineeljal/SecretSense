# Local API and demonstration site

Sprint 6 delivers a FastAPI service and a Next.js/TypeScript/Tailwind site with
home, scan, and results pages. Run both on the same machine as your browser. The
site sends text directly to the loopback API; Next.js never receives scan bodies.
This is a local demonstration, not a hosted or authenticated multi-user service.

## Start locally

Use Python 3.11+ and Node.js 22.13+ (Node 24 is configured in CI). From the root:

```sh
python -m pip install -e './core[dev,api]'
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 1 --no-access-log --no-proxy-headers --limit-concurrency 16 --backlog 32 --timeout-keep-alive 5
```

In another terminal:

```sh
cd web
npm ci
npm run build
npm run start
```

Open `http://127.0.0.1:3000`. Use `npm run dev` for frontend development. The scripts
disable Next.js telemetry and bind the site to loopback. Do not expose these
servers to the internet or enable request-body logging. API limits are per process;
run exactly one API worker. The startup command also bounds Uvicorn connections,
pending connections, and keep-alive idle time. Runtime dependencies require network
access during installation; scanning performs no remote requests.

Before starting or modifying the site, read the repository instructions and the
installed Next.js documentation under `web/node_modules/next/dist/docs/`. Version
16.3.8 is locked. The installed installation, layout, client-component, CSS, and
Playwright guides were consulted during implementation. Framework references:
[Next.js installation](https://nextjs.org/docs/app/getting-started/installation) and
[FastAPI error handling](https://fastapi.tiangolo.com/tutorial/handling-errors/).
The latter explains why default validation details must not echo scan inputs.

## API contract

| Route | Behavior |
| --- | --- |
| `POST /api/scan` | JSON object with required nonempty `content` string and optional `filename` string |
| `GET /api/health` | Process liveness, with `mode: local-demo`; does not perform a test scan |
| `GET /api/model/info` | Active engine, no model or scores, candidate retention policy, configured limits |

`filename` must contain 1–255 characters; it is accepted only for compatibility.
Every finding uses `submitted.txt`. Supplied filenames, raw values, and source
snippets never enter reports. Extra JSON fields, coercion, binary NULs, malformed
JSON, and invalid Unicode are rejected. Content must use `application/json` and
UTF-8. Compressed requests are unsupported. Archives, paths, Git history, model
uploads, and repository URLs are unsupported; `/api/scan/repo` returns 404.

A successful response uses the core JSON 1.2 report shape, with `complete: true`,
`files_scanned: 1`, all findings retained, no model scores, remediation guidance,
and every `masked_value` set to `[REDACTED]`. The API deliberately redacts more
than the CLI, which retains a short prefix/suffix for long values. A failure never
returns partial findings as a successful scan. No candidates is not a security
guarantee, and matches do not prove credential validity.

A value-free request example:

```sh
curl --silent http://127.0.0.1:8000/api/scan \
  --header 'Content-Type: application/json' \
  --data '{"content":"print(42)","filename":"example.py"}'
```

## Resource boundaries

| Boundary | Default |
| --- | --- |
| Total encoded HTTP request body | 1 MiB, including JSON syntax/escaping |
| Concurrent POST requests | 2, including body reads; no waiting queue |
| POST arrival rate | 30 per rolling minute across the process |
| Entire POST request deadline | 10 seconds, including body reading and worker cleanup |
| Scan worker deadline | 5 seconds, including worker startup/pipe communication |
| Report findings | 1,000; exceeding the limit fails the scan |
| Serialized worker output | 2 MiB; exceeding the limit fails the scan |

The ASGI boundary checks declared length and counts streamed bytes, so omitted or
misleading length headers do not bypass the cap. Rate bookkeeping is a bounded
in-memory deque, independent of client IP and untrusted forwarding headers.
Health/info GETs remain available when scan slots are occupied. POST requests to
unsupported routes also consume the shared rate budget.

Each admitted scan runs the trusted scanner module in a disposable Python
subprocess. Source is passed over stdin, not as command arguments or files. Only
redacted JSON leaves stdout; stderr is discarded. Deadline expiry or cancellation
kills and reaps the worker before releasing its slot. Limits bound work, not an
OS sandbox or a fixed resident-memory budget. OS process creation/termination and
synchronous parsing can add scheduling latency to deadlines. A client disconnect
after the upload does not necessarily cancel work immediately; the worker still
has its five-second deadline.

Errors are generic and omit validation inputs and exception details. Status codes:
400 invalid length/disconnection; 403 disallowed origin; 404 unsupported route;
413 excessive size; 415 unsupported media/encoding; 422 invalid input or report
limits; 429 rate exhausted; 503 concurrency exhausted; 504 deadline; 500 internal
failure. Rate/busy responses include `Retry-After: 60`. Scan responses and boundary
errors have `Cache-Control: no-store`. Uvicorn's own connection-limit failures can
use its generic 503 response.

Hosts are restricted to `localhost` and `127.0.0.1`. Browser origins are restricted
to their HTTP port-3000 variants. CORS is not authentication; local programs can
call the API directly. Browser requests always target `http://127.0.0.1:8000`.
Changing ports/hosts requires a reviewed configuration/code change. No proxy or
remote URL target can be selected by scan input.

## Browser behavior and privacy

The input form accepts pasted text or one file, reads files in browser memory,
rejects oversized/non-UTF-8/binary input, and checks the final JSON byte size.
Nothing is submitted until **Analyze text** is selected. Editing necessarily
shows the user's supplied input; results contain no source or complete values.
Input clears at submission, including failed scans. Retrying requires re-entering
text. Loading/disabled states prevent duplicate submissions and file-read races.
HTTP and connectivity errors show static messages, never a server error body.

Results show locations, rule severity, explanations, and expandable remediation.
Severity filtering only affects the view. The demo uses rules and entropy;
no numerical ML score, model performance badge, or credential validation is implied.
A fresh load of `/results` has an explicit empty state. The home preview is labeled
illustrative and contains redacted placeholders only.

Results live in React memory across in-site navigation. Reloading, leaving the
site, clearing results, or starting a new scan clears them. There is no localStorage,
sessionStorage, cookie, database, analytics, remote asset, or result URL payload.
Input is not kept in the shared session. Test traces/video/screenshots are disabled
because they could capture source input; use only synthetic text in automated tests.
Browser memory, developer tools, extensions, OS swap, and crash dumps remain outside
these application guarantees. Neither JavaScript nor Python guarantees memory erasure.

The layout supports mobile widths, keyboard navigation, a skip link, labeled
controls, status/error announcements, and reduced motion. Responses escape through
React. The site has frame restrictions, a no-referrer policy, and a CSP limited to
local assets and the loopback API. Next.js hydration needs inline scripts; this CSP
is defense in depth, not a replacement for escaping. Development additionally
permits eval for framework tooling.

## Validation and CI

From the root, with the full existing development environment installed:

```sh
ruff check core ml api .github/actions-runner
ruff format --check core ml api .github/actions-runner
pytest core/tests ml/tests api/tests --cov=secretsense --cov=ml.scripts --cov=api --cov-report=term-missing --cov-fail-under=85
python -m build core
pip-audit --skip-editable
```

From `web/`:

```sh
npm ci
npm run lint
npm run format:check
npm run build
npm run typecheck
npx playwright install chromium
npm test
npm audit
```

Playwright starts both local production servers itself, using `../.venv/bin/python`.
Set `SECRETSENSE_PYTHON` to an interpreter with the core and API dependencies if
needed. Keep ports 3000 and 8000 free. Tests exercise Chromium desktop and mobile
emulation, real API scans, masking, upload limits, error handling, filtering,
remediation, memory-only results, and responsive/reduced-motion behavior. These
are not native iOS/Safari tests. API tests additionally verify streamed limits,
slow uploads, admission, process death/cancellation, and value-free failures.

The Python CI matrix includes API tests, and a separate Node 24 job builds/audits
the site and runs browser tests. Dependabot includes npm. See
[the progress log](progress.md) for checks actually run locally; configuration is
not evidence of a remote CI run. The core wheel contains scanner code; `api/` and
`web/` run from this checkout and are not claimed as published application packages.
