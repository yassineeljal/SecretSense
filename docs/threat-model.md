# Threat model

## Current local scanner

Scanned files and filenames are untrusted. Their contents are read, never executed.
Scanning makes no network requests and creates no content cache. Only UTF-8 text
is supported. Per-file reads, traversal entries, ignore-file size, and directory
depth are bounded. Symlinks are skipped; on supported systems, final file opens use
`O_NOFOLLOW` and `O_NONBLOCK`, followed by a regular-file check.

These controls do not make traversal a sandbox: another local process can change
ancestor directories during a scan. Use a stable checkout for untrusted input.
There is no global byte budget, scan deadline, archive extraction, repository URL
fetcher, or Git-history traversal in this version. Built-in exclusions and
`.gitignore` can hide secrets; inspect scan scope and scan ignored files explicitly
when necessary. The scanner does not defend against a malicious ignore policy.

Reports omit raw matches and source context, mask short values completely, and
show only four leading/trailing characters for longer values. Paths and locations
remain visible, including sensitive information embedded in filenames. Terminal
control characters in paths are escaped. Generic I/O errors omit exception details.
Memory and crash dumps may retain source input; Python strings cannot be reliably
zeroed after scanning. A clean report is not a security guarantee.

## Planned hosted demonstration

Before shipping the API, enforce request sizes, rate limits, scan deadlines, and
concurrency limits. Process inputs only in memory, disable body logging and
persistence, and never display whole detected secrets. Public-repository fetching
needs independent SSRF protection, clone/size/time limits, and safe cleanup.
Archives require decompression limits before support can be considered.

Optional Ollama requests must redact values before transmission. A model artifact
must come from the project and pass a trusted hash check before deserialization;
a hash supplied alongside an untrusted pickle does not establish trust.

Dependency checks are configured through Dependabot and `pip-audit`; Gitleaks
checks the working directory through pre-commit and in CI. Generated Python
caches are excluded from Gitleaks because tests construct synthetic token values.
