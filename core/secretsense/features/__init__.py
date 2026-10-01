"""Versioned numeric features derived exclusively from a value and its context."""

import re

from secretsense.scanner.entropy import shannon_entropy
from secretsense.scanner.patterns import RULES

FEATURE_VERSION = 1
FEATURE_NAMES = (
    "length",
    "entropy",
    "unique_ratio",
    "lower_ratio",
    "upper_ratio",
    "digit_ratio",
    "symbol_ratio",
    "hex_only",
    "has_newline",
    "format_match",
    "secret_name",
    "placeholder_marker",
    "environment_reference",
)
SECRET_NAME = re.compile(r"password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key", re.I)


def extract_features(
    value: str, context: str, *, value_start: int | None = None
) -> tuple[float, ...]:
    """Return a fixed numeric vector, without labels, filenames, IDs, or provenance.

    Context is limited to the 200 characters preceding the specified occurrence,
    or the first occurrence when no offset is supplied.
    Features are heuristics; none prove whether a credential is valid.
    """
    if not value or (value_start is None and value not in context):
        raise ValueError("Feature input requires a nonempty value in context; content omitted.")
    start = context.index(value) if value_start is None else value_start
    if start < 0 or context[start : start + len(value)] != value:
        raise ValueError("Feature offset does not match the value; content omitted.")
    size = len(value)
    prefix = context[max(0, start - 200) : start]
    lower = value.lower()
    return (
        float(size),
        shannon_entropy(value),
        len(set(value)) / size,
        sum(char.islower() for char in value) / size,
        sum(char.isupper() for char in value) / size,
        sum(char.isdigit() for char in value) / size,
        sum(not char.isalnum() for char in value) / size,
        float(all(char in "0123456789abcdefABCDEF" for char in value)),
        float("\n" in value),
        float(any(rule.pattern.search(value) for rule in RULES)),
        float(bool(SECRET_NAME.search(prefix))),
        float(lower.startswith(("your_", "example", "changeme", "placeholder", "dummy_"))),
        float(lower.startswith(("os.getenv", "os.environ", "process.env", "${"))),
    )
