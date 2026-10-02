# Security policy

SecretSense is an early-stage scanner. Findings are candidates, not proof that a
credential is active. A clean report does not establish that a repository is safe.
Only the latest development version is maintained at this stage.

Do not post real credentials or private source code in public issues. If GitHub
private vulnerability reporting is enabled, use the repository's **Security →
Report a vulnerability** flow. If it is unavailable, open a minimal issue asking
for a private contact channel without including exploit details or sensitive data.

If a real credential is exposed, revoke or rotate it with the provider and review
its use. Deleting a file does not remove the credential from Git history.

The current scanner runs locally, makes no network calls, and does not write
scanned contents to disk. Console, JSON, HTML, and SARIF reports mask detected values. Reports
still include filenames, locations, service labels, and parts of matched values;
treat them as sensitive. Local processes and crash dumps may inspect process
memory. See [the threat model](docs/threat-model.md) for limits and planned controls.

The loopback API uses disposable bounded workers and fully redacts values and
filenames. The local browser demo keeps redacted reports in memory. Public
portfolio mode accepts no scan input; the API is not approved for public ingress.
See the [privacy policy](PRIVACY.md), [API guide](docs/api-and-web.md), and
[hosting/release preparation](docs/release.md). No application-level guarantee
extends to browser extensions, OS swap, or infrastructure logging.
