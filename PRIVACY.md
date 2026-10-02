# Privacy policy

Effective for the development checkout on 2026-10-01. This describes application
behavior, not a hosted-service contract. No public scan service is deployed.

## Local CLI and API

Scanning stays on the machine running the Python scanner. It does not execute
input, validate credentials with providers, fetch repositories, or send telemetry.
Installing dependencies can contact package registries; that is separate from
scanning. The scanner does not persist source input. Explicitly redirected reports
are files under the user's control and should be treated as sensitive.

The demo sends input directly from the browser to the loopback API, not through
Next.js. Its disposable worker receives source through pipes. API error messages
are generic; the documented startup disables access logs. API values and filenames
are fully redacted. CLI reports retain paths, locations, and masked partial values;
neither interface includes complete detected values or source snippets.

## Browser lifecycle

Input clears at submission. Redacted results remain in React memory during in-site
navigation and clear on reload, site exit, explicit clearing, or another scan.
No application cookies, localStorage, sessionStorage, analytics, external fonts,
or remote assets are used. Copy buttons write only displayed setup commands to
the clipboard at the user's request. Clipboard content remains under OS control.

Application-level non-persistence is not secure erasure. Extensions, developer
tools, other local processes, OS swap, backups, and crash dumps can expose memory.
Do not enable browser traces, video, or source screenshots for real scan content.

## Portfolio hosting preparation

The portfolio build accepts no source or upload and makes no requests to a scan
API. It contains documentation and aggregate synthetic evaluation results only.
Outbound documentation links contact GitHub when followed. A future web host may
process IP addresses, URLs, request metadata, and infrastructure logs; its actual
retention, region, operator contact, and terms must be recorded before deployment.
No claim of zero host logging is made. Repository issues and interactions with
GitHub are subject to GitHub's own policies.

## Questions and reporting

Use the repository's issue tracker for non-sensitive privacy questions. For
vulnerabilities, follow [SECURITY.md](SECURITY.md); do not attach credentials,
private source, or exploit details publicly. There is no application-held account
or server-side scan history to retrieve or delete.
