"""Shannon entropy in bits per character."""

from collections import Counter
from math import log2


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    size = len(value)
    return -sum((count / size) * log2(count / size) for count in Counter(value).values())
