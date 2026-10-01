"""Shared data contracts and deterministic generation helpers."""

import hashlib
import random
import string
from dataclasses import dataclass, field

VERSION = "1"
DEFAULT_SEED = 20260930
DEFAULT_PER_FAMILY = 300
ALPHANUMERIC = string.ascii_letters + string.digits


@dataclass(frozen=True)
class Example:
    # Keep training material out of object representations and error messages.
    text: str = field(repr=False)
    value: str = field(repr=False)
    label: int
    category: str
    template_family: str
    source_group: str
    source_id: str
    review_status: str
    provenance: str = "locally-authored-synthetic"
    license: str = "MIT"

    @property
    def sample_id(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


def family_rng(seed: int, family: str) -> random.Random:
    digest = hashlib.sha256(f"{VERSION}:{seed}:{family}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def random_text(rng: random.Random, length: int, alphabet: str = ALPHANUMERIC) -> str:
    return "".join(rng.choice(alphabet) for _ in range(length))


def assignment(rng: random.Random, name: str, value: str) -> str:
    """Vary wrappers within a family; never use wrappers as split groups."""
    if "\n" in value:
        return f'{name} = """{value}"""'
    return rng.choice((f'{name} = "{value}"', f'{name}: "{value}"', f'{{"{name}": "{value}"}}'))


def check_count(count: int) -> None:
    if not 1 <= count <= 1000:
        raise ValueError("Examples per family must be between 1 and 1000.")
