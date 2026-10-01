"""Static, value-free response guidance. No provider requests or automatic changes."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Playbook:
    title: str
    steps: tuple[str, ...]


# Deliberately describe credential ownership, not changing provider UI labels.
ACTIONS = {
    "AWS": (
        "Deactivate the affected IAM access key; replace it and review CloudTrail "
        "activity. For temporary credentials, revoke the issuing sessions where "
        "supported."
    ),
    "GitHub": (
        "Revoke the token or application authorization in GitHub; review its scopes "
        "and account or organization audit activity."
    ),
    "GitLab": (
        "Revoke the personal, project, or group access token in GitLab; review its "
        "permissions and audit activity."
    ),
    "Stripe": (
        "Rotate the affected Stripe API key; distinguish test and live mode and "
        "review API request logs."
    ),
    "Slack": (
        "Revoke the affected Slack token or app authorization; reinstall or "
        "reauthorize only the required scopes and review workspace activity."
    ),
    "Google": (
        "Replace and delete the affected Google Cloud API key; restrict the "
        "replacement by API and application and review usage."
    ),
    "SendGrid": (
        "Delete the exposed SendGrid API key, create a restricted replacement, and "
        "review sending activity."
    ),
    "npm": (
        "Revoke the npm access token; review package publication and use narrowly "
        "scoped publishing credentials."
    ),
    "PyPI": (
        "Revoke the PyPI API token; review release history and prefer trusted "
        "publishing where available."
    ),
    "Shopify": (
        "Revoke or rotate the affected Shopify app credential or access token "
        "through its owning app; review store access and app permissions."
    ),
    "DigitalOcean": (
        "Revoke the DigitalOcean personal access token; replace it with minimum "
        "permissions and review account activity."
    ),
    "Grafana": (
        "Revoke the affected Grafana service account token or API key in its owning "
        "instance; review permissions and activity."
    ),
    "Hugging Face": (
        "Delete or refresh the Hugging Face access token; review repository access "
        "and use a restricted replacement."
    ),
    "Docker Hub": (
        "Deactivate or delete the Docker Hub access token; replace it and review "
        "image publication and account activity."
    ),
    "Mailgun": (
        "Revoke or rotate the affected Mailgun API key; review domain permissions "
        "and sending activity."
    ),
    "Private key": (
        "Replace the key pair and revoke affected certificates or authorized public "
        "keys; identify every system trusting the exposed key."
    ),
    "JWT": (
        "Identify the issuer and invalidate the affected session or token where "
        "supported. Rotate signing keys only if those keys were exposed; a JWT "
        "alone does not establish that."
    ),
}


def get_playbook(service: str) -> Playbook:
    action = ACTIONS.get(
        service,
        (
            "Identify the credential owner, rotate or revoke the affected "
            "credential, and review access logs for misuse."
        ),
    )
    return Playbook(
        title=f"Respond to a potential {service} exposure",
        steps=(
            (
                "Triage locally without sending the value to a validation service; "
                "format matches do not prove validity."
            ),
            action,
            (
                "Update dependent applications using a secret manager or protected "
                "environment configuration; verify recovery locally."
            ),
            (
                "Remove the exposed value from tracked files and coordinate any "
                "history cleanup after revocation. Deleting a commit does not "
                "revoke a credential."
            ),
        ),
    )
