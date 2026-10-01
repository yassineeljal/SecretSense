"""Format heuristics, not provider validation or exhaustive format coverage."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    id: str
    service: str
    pattern: re.Pattern[str]
    severity: str = "high"


def token_rule(rule_id: str, service: str, expression: str) -> Rule:
    return Rule(rule_id, service, re.compile(r"(?<![\w-])(?:" + expression + r")(?![\w-])"))


RULES = (
    token_rule("aws-access-key", "AWS", r"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    token_rule("github-token", "GitHub", r"gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82}"),
    token_rule("gitlab-token", "GitLab", r"glpat-[A-Za-z0-9_-]{20}"),
    token_rule("stripe-key", "Stripe", r"[sr]k_(?:live|test)_[A-Za-z0-9]{24,128}"),
    token_rule("slack-token", "Slack", r"xox[baprs]-[A-Za-z0-9-]{10,100}"),
    token_rule("google-api-key", "Google", r"AIza[A-Za-z0-9_-]{35}"),
    token_rule("sendgrid-key", "SendGrid", r"SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}"),
    token_rule("npm-token", "npm", r"npm_[A-Za-z0-9]{36}"),
    token_rule("pypi-token", "PyPI", r"pypi-[A-Za-z0-9_-]{50,1000}"),
    token_rule("shopify-token", "Shopify", r"shp(?:at|ss|ca|pa)_[a-fA-F0-9]{32}"),
    token_rule("digitalocean-token", "DigitalOcean", r"dop_v1_[a-f0-9]{64}"),
    token_rule("grafana-token", "Grafana", r"glc_[A-Za-z0-9_+/=-]{32,512}"),
    token_rule("huggingface-token", "Hugging Face", r"hf_[A-Za-z0-9]{34}"),
    token_rule("docker-token", "Docker Hub", r"dckr_pat_[A-Za-z0-9_-]{27}"),
    token_rule("mailgun-key", "Mailgun", r"key-[a-f0-9]{32}"),
    Rule(
        "private-key",
        "Private key",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
        "critical",
    ),
    token_rule("jwt", "JWT", r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
)

# Restrict entropy to a literal assigned to a secret-like name. Avoid treating
# arbitrary hashes, UUIDs, and build identifiers as secrets just for being random.
ASSIGNMENT = re.compile(
    r"""(?i)\b[\w.-]{0,80}(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key)"""
    r"""[\w.-]{0,80}["']?\s*[:=]\s*["']?(?P<value>[A-Za-z0-9_+/!@#$%^&*?.=~-]{8,256})"""
    r"""(?=[\s"',;\]}]|$)"""
)
