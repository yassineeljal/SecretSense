"""Transient candidate offsets; no raw values are retained in result objects."""

from dataclasses import dataclass

from secretsense.scanner.entropy import shannon_entropy
from secretsense.scanner.patterns import ASSIGNMENT, RULES


@dataclass(frozen=True)
class Candidate:
    start: int
    end: int
    rule_id: str
    service: str
    severity: str
    explanation: str


def extract_candidates(content: str) -> list[Candidate]:
    """Apply the scanner's existing rules and entropy policy without retaining input."""
    candidates = []
    occupied = []
    for rule in RULES:
        for match in rule.pattern.finditer(content):
            occupied.append(match.span())
            candidates.append(
                Candidate(
                    *match.span(),
                    rule.id,
                    rule.service,
                    rule.severity,
                    "Matches a credential format; validity has not been checked.",
                )
            )
    for match in ASSIGNMENT.finditer(content):
        start, end = match.span("value")
        value = match.group("value")
        if any(start < other_end and end > other_start for other_start, other_end in occupied):
            continue
        if value.lower().startswith(("your_", "example", "changeme", "placeholder", "process.env")):
            continue
        if value.startswith(("$", "os.getenv", "os.environ")):
            continue
        if shannon_entropy(value) >= 3.5:
            candidates.append(
                Candidate(
                    start,
                    end,
                    "generic-secret",
                    "Generic",
                    "medium",
                    "High-entropy literal assigned to a secret-like name; review manually.",
                )
            )
    return sorted(candidates, key=lambda item: (item.start, item.rule_id))
