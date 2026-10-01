"""Invent credential-shaped examples; never contact credential providers."""

import base64
import json
import random
import string

from ml.scripts.common import (
    DEFAULT_PER_FAMILY,
    DEFAULT_SEED,
    Example,
    assignment,
    check_count,
    family_rng,
    random_text,
)

FAMILIES = (
    "aws-access-key",
    "github-token",
    "gitlab-token",
    "stripe-key",
    "slack-token",
    "jwt",
    "private-key-shape",
    "database-password",
    "google-api-key",
    "sendgrid-key",
)


def encode_json(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def make_value(family: str, rng: random.Random) -> tuple[str, str]:
    if family == "aws-access-key":
        return "aws_access_key", "AKIA" + random_text(
            rng, 16, string.ascii_uppercase + string.digits
        )
    if family == "github-token":
        return "github_token", "ghp_" + random_text(rng, 36)
    if family == "gitlab-token":
        return "gitlab_token", "glpat-" + random_text(rng, 20)
    if family == "stripe-key":
        return "stripe_key", "sk_" + rng.choice(("test_", "live_")) + random_text(rng, 32)
    if family == "slack-token":
        parts = [random_text(rng, 12, string.digits) for _ in range(2)]
        return "slack_token", "xoxb-" + "-".join([*parts, random_text(rng, 24)])
    if family == "jwt":
        header = encode_json({"alg": "HS256", "typ": "JWT"})
        payload = encode_json({"sub": random_text(rng, 20), "iss": "https://issuer.invalid"})
        # Random bytes, not a signature; there is no signing key or live issuer.
        signature = base64.urlsafe_b64encode(rng.randbytes(32)).decode().rstrip("=")
        return "auth_token", ".".join((header, payload, signature))
    if family == "private-key-shape":
        # Deliberately not DER and not a usable cryptographic key.
        body = base64.b64encode(b"synthetic-not-a-key:" + rng.randbytes(64)).decode()
        return (
            "private_key",
            "-----BEGIN " + "PRIVATE KEY-----\n" + body + "\n-----END PRIVATE KEY-----",
        )
    if family == "database-password":
        return "database_password", random_text(rng, rng.choice((16, 24, 32, 48)))
    if family == "google-api-key":
        return "google_api_key", "AIza" + random_text(rng, 35)
    if family == "sendgrid-key":
        return "sendgrid_key", "SG." + random_text(rng, 22) + "." + random_text(rng, 43)
    raise ValueError("Unknown positive template family.")


def generate(count: int = DEFAULT_PER_FAMILY, seed: int = DEFAULT_SEED) -> list[Example]:
    check_count(count)
    examples = []
    for family in FAMILIES:
        rng = family_rng(seed, family)
        for _ in range(count):
            name, value = make_value(family, rng)
            examples.append(
                Example(
                    text=assignment(rng, name, value),
                    value=value,
                    label=1,
                    category=family,
                    template_family=family,
                    source_group=f"synthetic:{family}",
                    source_id=f"generate_fake_secrets.py:{family}:v1",
                    review_status="synthetic-positive-by-construction",
                )
            )
    return examples
