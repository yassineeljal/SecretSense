# Responding to potential exposures

Every finding now carries a static playbook in JSON schema 1.2. Console and HTML
show its steps; SARIF attaches guidance to the rule's help. Guidance is advisory:
SecretSense never contacts a provider, changes credentials, edits files, or rewrites
Git history. A format match or ML score does not establish credential validity.

Triage locally, identify the owning service and environment, and revoke or rotate
an exposed credential through your normal incident process. Update dependent
applications with a secret manager or protected configuration and review activity.
Coordinate history cleanup after revocation: removing a file or commit does not
invalidate the credential, remove existing clones, or undo past access.

| Detected service | Specific response |
| --- | --- |
| AWS | Deactivate and replace long-term access keys; assess issued temporary sessions and CloudTrail activity. |
| GitHub | Revoke the affected token/app authorization and inspect account or organization activity. |
| GitLab | Revoke the owning personal, project, or group token and review permissions. |
| Stripe | Rotate the affected key, distinguish live/test mode, and inspect API logs. |
| Slack | Revoke the token/app authorization and review scopes before reauthorization. |
| Google | Replace/delete the API key and restrict the replacement's APIs and applications. |
| SendGrid | Delete the exposed key, restrict the replacement, and inspect sending activity. |
| npm | Revoke the access token and inspect package publication. |
| PyPI | Revoke the API token and inspect releases; consider trusted publishing. |
| Shopify | Revoke/rotate through the owning app and inspect store access. |
| DigitalOcean | Revoke the personal access token and inspect account activity. |
| Grafana | Revoke the service account token/API key in the owning instance. |
| Hugging Face | Delete/refresh the access token and inspect repository access. |
| Docker Hub | Deactivate/delete the token and inspect image publication. |
| Mailgun | Revoke/rotate the key and inspect sending activity. |
| Private key | Replace the key pair and revoke the corresponding certificates or trusted public keys. |
| JWT | Identify the issuer and invalidate the affected session where supported; rotate signing keys only if those keys were exposed. |
| Generic entropy candidate | Identify the owner before choosing a rotation/revocation procedure. |

Provider procedures differ by credential type and account permissions. See the
[AWS access-key guide](https://docs.aws.amazon.com/IAM/latest/UserGuide/securing_access-keys.html),
[AWS session revocation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_revoke-sessions.html),
[GitHub revocation guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/revoking-your-credentials),
and [Stripe incident guidance](https://support.stripe.com/questions/protecting-against-compromised-api-keys).
These references explain response procedures; the scanner never calls them with
findings or detected values.
