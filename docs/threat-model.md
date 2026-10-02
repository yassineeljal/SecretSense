# Threat model

## Current local scanner

Scanned files and filenames are untrusted. Their contents are read, never executed.
Scanning makes no network requests and creates no content cache. Only UTF-8 text
is supported. Per-file reads, traversal entries, ignore-file size, and directory
depth are bounded. Symlinks are skipped; on supported systems, final file opens use
`O_NOFOLLOW` and `O_NONBLOCK`, followed by a regular-file check.

These controls do not make traversal a sandbox: another local process can change
ancestor directories during a scan. Use a stable checkout for untrusted input.
Working-tree scanning has no global byte budget or deadline. There is no archive
extraction or repository URL fetcher. Git-history limits are described below. Built-in exclusions and
`.gitignore` can hide secrets; inspect scan scope and scan ignored files explicitly
when necessary. The scanner does not defend against a malicious ignore policy.

Reports omit raw matches and source context, mask short values completely, and
show only four leading/trailing characters for longer values. Paths and locations
remain visible, including sensitive information embedded in filenames. Terminal
control characters in paths are escaped. Generic I/O errors omit exception details.
Memory and crash dumps may retain source input; Python strings cannot be reliably
zeroed after scanning. A clean report is not a security guarantee.

## Local experimental model

The optional training command accepts the authored synthetic dataset, verifies its
checksum and grouped row contract, and emits only aggregate results. Numeric
features accept only values and context, excluding label/provenance metadata.
Transient candidate objects retain offsets, not values. Training artifacts are
local and excluded from Git and package distributions.

The explicit trusted loader bounds model reads to 32 MiB and verifies the hash
before deserializing the same bytes, then validates the feature schema. This is
not a sandbox or a signature: an attacker-controlled pickle with an accompanying
hash is unsafe. Only locally produced or independently trusted artifacts may be
loaded. CLI model loading requires both an explicit path and trusted digest;
there is no automatic download or discovery. Regular-file checks and nonblocking
opens reject special files; final symlinks are rejected where `O_NOFOLLOW` exists.
Feature, fitted model, binary class order, and threshold schemas are validated.
Deserialization warnings and inference exceptions become generic value-free errors.
Model file validation does not sandbox pickle execution; trust remains essential.

Experimental scores are uncalibrated, and synthetic held-out results do not
establish real-world accuracy. All candidates remain visible regardless of score;
inference failure retains unscored findings and marks the scan incomplete.
HTML reports escape all dynamic text, have no scripts or remote assets, and include
a restrictive Content Security Policy. User-chosen report files should be written
outside scan targets. JSON and HTML expose the same masked values and filenames;
neither includes source snippets.

## Local API and browser demonstration

Sprint 6 enforces streaming body size, request/worker deadlines, per-process
rate and concurrency limits, and report caps. Worker processes are killed and
reaped on deadline or cancellation. Input is in-memory only, passed over pipes;
worker stderr is discarded and unexpected errors become static messages before
they reach the ASGI server logger. Start Uvicorn with access logging and proxy
headers disabled as documented in [the API/site guide](api-and-web.md).

The API fully redacts values and substitutes a fixed filename. Browser results
are held in React memory only; input clears on submission. No content is sent to
Next.js, remote assets, analytics, providers, or model endpoints. Browser editing
necessarily displays supplied source. Browser extensions, developer tools, OS
swap, and crash dumps can still observe it; memory cannot be securely erased.

The API is loopback-only by startup convention, with local Host and Origin checks.
CORS is not authentication. Per-process limits require one worker and are not
an OS memory sandbox. Parser/OS scheduling can add deadline latency; disconnected
clients may occupy a worker until its bounded scan finishes. This unauthenticated
service is not approved for public hosting. A deployment needs authentication,
TLS, ingress/process resource limits, logging review, and a multi-worker limit
strategy. Public-repository fetching needs independent SSRF protection,
clone/size/time limits, and safe cleanup. Archives need decompression limits;
neither is supported.

Optional Ollama requests must redact values before transmission. A model artifact
must come from the project and pass a trusted hash check before deserialization;
a hash supplied alongside an untrusted pickle does not establish trust.

Dependency checks are configured through Dependabot and `pip-audit`; Gitleaks
checks the working directory through pre-commit and in CI. Generated Python
caches are excluded from Gitleaks because tests construct synthetic token values.


## Local Git history and CI reports

History uses raw Git object reads with byte/output/entry/commit caps and a deadline;
there is no checkout, textconv, smudge filter, hook, submodule traversal, or lazy
fetch. Git receives argument lists without a shell, refs are resolved with
`--end-of-options`, stderr is discarded, inherited Git environment configuration
is removed, and all transport protocols are denied. It still depends on a trusted,
patched local Git executable and does not sandbox Git itself. Linked worktree and
alternate local object stores remain local Git storage, not a filesystem sandbox.
Use a stable repository: another process can modify metadata during scanning.
Deadlines terminate Git I/O and are checked between bounded blobs; Python analysis
and optional prediction are not forcibly interrupted. Missing objects, truncated
or shallow histories, and exhausted bounds are explicitly incomplete.

Reports retain commit/blob IDs and paths, never author identities, commit messages,
source snippets, or complete matched values. SARIF fingerprints hash location
metadata only. Paths may contain sensitive information, as in working-tree reports.
The composite Action scans locally and writes temporary SARIF, with no automatic
upload. Installation uses network package downloads; source scanning does not.
Action inputs are data passed through environment variables, not shell fragments.
Pin a reviewed Action commit and avoid running an untrusted checkout's local Action
in a privileged workflow. Remediation steps are static advice, not executed commands.

## Portfolio and release preparation

Public portfolio builds have no scan form/upload or API request path in the rendered
scanner page; CSP also excludes the loopback API. Hosting a local-mode build is not
a supported public deployment. No Python service is deployed by the Vercel config.
Host request metadata and infrastructure logs are outside the local non-persistence
guarantee and must be documented before launch. The release workflow defaults to
build-only and grants OIDC only to a separate publish job; publication additionally
requires an enabled repository variable, matching version tag, successful push CI
for that commit, and separately configured protected registry environments.
