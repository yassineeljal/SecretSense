"""Create reviewed benign templates locally; no repositories are downloaded."""

import hashlib
import json
import random
import uuid
from pathlib import Path

from ml.scripts.common import (
    DEFAULT_PER_FAMILY,
    DEFAULT_SEED,
    Example,
    assignment,
    check_count,
    family_rng,
    random_text,
)

CATALOG = Path(__file__).resolve().parents[1] / "data" / "negative_templates.json"
FAMILIES = (
    "documentation-placeholder",
    "environment-reference",
    "uuid",
    "content-hash",
    "build-id",
    "documentation-url",
    "test-dummy",
    "version",
    "css-color",
    "numeric-id",
)


def make_value(family: str, rng: random.Random, index: int) -> tuple[str, str, bool]:
    suffix = random_text(rng, 12)
    if family == "documentation-placeholder":
        return "api_key", f"your_key_here_{index}_{suffix}", False
    if family == "environment-reference":
        name = f"SERVICE_{index}_{suffix.upper()}_TOKEN"
        expression = rng.choice((f'os.getenv("{name}")', f"process.env.{name}", f"${{{name}}}"))
        return "api_token", expression, True
    if family == "uuid":
        return "request_id", str(uuid.UUID(int=rng.getrandbits(128), version=4)), False
    if family == "content-hash":
        return "content_hash", hashlib.sha256(suffix.encode()).hexdigest(), False
    if family == "build-id":
        return "build_id", f"build-{index}-{suffix}", False
    if family == "documentation-url":
        return "docs_url", f"https://docs.example.invalid/guide/{suffix}/{index}", False
    if family == "test-dummy":
        return "password", f"dummy_for_test_{index}_{suffix}", False
    if family == "version":
        return "package_version", f"{rng.randrange(10)}.{index}.{rng.randrange(100)}", False
    if family == "css-color":
        # A palette, to retain uniqueness without inventing nonstandard color lengths.
        colors = ["#" + random_text(rng, 6, "0123456789abcdef") for _ in range(3)]
        return "theme_colors", " ".join(colors), False
    if family == "numeric-id":
        return "issue_id", str(100000000000 + index * 1000000 + rng.randrange(1000000)), False
    raise ValueError("Unknown negative template family.")


def collect(count: int = DEFAULT_PER_FAMILY, seed: int = DEFAULT_SEED) -> list[Example]:
    check_count(count)
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if set(catalog["families"]) != set(FAMILIES):
        raise ValueError("Negative review catalog does not match the generator families.")
    examples = []
    for family in FAMILIES:
        review = catalog["families"][family]
        if review["label"] != 0 or not review["rationale"] or not review["limitations"]:
            raise ValueError("Negative template review is incomplete.")
        rng = family_rng(seed, family)
        for index in range(count):
            name, value, expression = make_value(family, rng, index)
            text = f"{name} = {value}" if expression else assignment(rng, name, value)
            examples.append(
                Example(
                    text=text,
                    value=value,
                    label=0,
                    category=family,
                    template_family=family,
                    source_group=f"synthetic:{family}",
                    source_id=f"collect_false_positives.py:{family}:v1",
                    review_status="template-reviewed-by-local-inspection",
                )
            )
    return examples
