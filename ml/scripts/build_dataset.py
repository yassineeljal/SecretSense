"""Build a balanced synthetic CSV and a value-free reproducibility manifest."""

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from pathlib import Path

from ml.scripts.collect_false_positives import CATALOG, collect
from ml.scripts.common import DEFAULT_PER_FAMILY, DEFAULT_SEED, VERSION, Example
from ml.scripts.generate_fake_secrets import generate

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("sample_id", *Example.__dataclass_fields__, "split")
SPLITS = {"train": 0.6, "validation": 0.2, "test": 0.2}


def clean(examples: list[Example]) -> tuple[list[Example], int]:
    """Normalize line endings, reject invalid labels, and deduplicate text/values."""
    unique = []
    seen_text: dict[str, Example] = {}
    seen_value: dict[str, Example] = {}
    for example in examples:
        example = replace(
            example,
            text=example.text.replace("\r\n", "\n").replace("\r", "\n").strip(),
            value=example.value.replace("\r\n", "\n").replace("\r", "\n").strip(),
        )
        if (
            example.label not in (0, 1)
            or not example.text
            or not example.value
            or example.value not in example.text
            or not all(
                (example.template_family, example.source_group, example.source_id, example.license)
            )
        ):
            raise ValueError("Invalid dataset example; content omitted.")
        previous = [seen_text.get(example.text), seen_value.get(example.value)]
        for match in previous:
            if match is not None and (
                match.label != example.label
                or match.template_family != example.template_family
                or match.source_group != example.source_group
            ):
                # Silently dropping cross-group duplicates would conceal leakage.
                raise ValueError("Conflicting duplicate labels or provenance; content omitted.")
        if any(match is not None for match in previous):
            continue
        unique.append(example)
        seen_text[example.text] = example
        seen_value[example.value] = example
    return unique, len(examples) - len(unique)


def assign_splits(examples: list[Example], seed: int) -> dict[str, str]:
    """Keep connected source groups AND template families together."""
    parents: dict[str, str] = {}

    def find(key: str) -> str:
        parents.setdefault(key, key)
        while parents[key] != key:
            parents[key] = parents[parents[key]]
            key = parents[key]
        return key

    for example in examples:
        source = find("source:" + example.source_group)
        template = find("template:" + example.template_family)
        parents[max(source, template)] = min(source, template)
    groups: dict[str, list[Example]] = defaultdict(list)
    for example in examples:
        groups[find("source:" + example.source_group)].append(example)

    totals = Counter(example.label for example in examples)
    counts = {split: Counter() for split in SPLITS}
    assignment = {}
    # Sort by size, then a seeded metadata hash. No dependence on value or input order.
    order = sorted(
        groups,
        key=lambda group: (
            -len(groups[group]),
            hashlib.sha256(f"{seed}:{group}".encode()).hexdigest(),
        ),
    )
    for group in order:
        labels = Counter(example.label for example in groups[group])
        split = max(
            SPLITS,
            key=lambda name: sum(
                count * (totals[label] * SPLITS[name] - counts[name][label])
                for label, count in labels.items()
            ),
        )
        counts[split].update(labels)
        for example in groups[group]:
            assignment[example.sample_id] = split
    if any(not counts[split][label] for split in SPLITS for label in (0, 1)):
        raise ValueError("Not enough independent groups for both labels in every split.")
    return assignment


def validate_rows(rows: list[dict]) -> None:
    """Check CSV integrity without including row contents in failures."""
    if not rows:
        raise ValueError("Dataset is empty.")
    seen_ids: set[str] = set()
    seen_values: set[str] = set()
    memberships: dict[tuple[str, str], set[str]] = defaultdict(set)
    labels = Counter()
    split_labels = Counter()
    for row in rows:
        if set(row) != set(FIELDS):
            raise ValueError("Invalid dataset columns.")
        label = str(row["label"])
        split = row["split"]
        if label not in ("0", "1") or split not in SPLITS:
            raise ValueError("Invalid label or split.")
        if not row["value"] or row["value"] not in row["text"]:
            raise ValueError("Invalid value/context relationship; content omitted.")
        digest = hashlib.sha256(row["text"].encode()).hexdigest()
        if digest != row["sample_id"] or digest in seen_ids or row["value"] in seen_values:
            raise ValueError("Duplicate example or invalid content checksum; content omitted.")
        seen_ids.add(digest)
        seen_values.add(row["value"])
        for column in ("source_group", "template_family"):
            if not row[column]:
                raise ValueError("Missing grouping metadata.")
            memberships[column, row[column]].add(split)
        labels[label] += 1
        split_labels[split, label] += 1
    if any(len(splits) != 1 for splits in memberships.values()):
        raise ValueError("Source or template groups overlap across splits.")
    if labels["0"] != labels["1"]:
        raise ValueError("Dataset labels are not balanced.")
    if any(not split_labels[split, label] for split in SPLITS for label in ("0", "1")):
        raise ValueError("Every split must contain both labels.")


def build(count: int = DEFAULT_PER_FAMILY, seed: int = DEFAULT_SEED) -> tuple[bytes, dict]:
    examples, removed = clean(generate(count, seed) + collect(count, seed))
    splits = assign_splits(examples, seed)
    rows = [
        {"sample_id": example.sample_id, **asdict(example), "split": splits[example.sample_id]}
        for example in sorted(examples, key=lambda example: example.sample_id)
    ]
    validate_rows(rows)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    data = buffer.getvalue().encode("utf-8")
    source_paths = sorted((ROOT / "scripts").glob("*.py")) + [CATALOG]
    manifest = {
        "schema_version": 1,
        "generator_version": VERSION,
        "seed": seed,
        "examples_per_family": count,
        "rows": len(rows),
        "label_counts": dict(sorted(Counter(str(row["label"]) for row in rows).items())),
        "duplicates_removed": removed,
        "dataset_sha256": hashlib.sha256(data).hexdigest(),
        "sources": [
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in source_paths
        ],
        "split_policy": "Connected source/template groups; seeded ordering; 60/20/20 targets.",
        "splits": {
            split: {
                "rows": sum(row["split"] == split for row in rows),
                "label_counts": dict(
                    sorted(
                        Counter(str(row["label"]) for row in rows if row["split"] == split).items()
                    )
                ),
                "template_families": sorted(
                    {row["template_family"] for row in rows if row["split"] == split}
                ),
                "source_groups": sorted(
                    {row["source_group"] for row in rows if row["split"] == split}
                ),
            }
            for split in SPLITS
        },
        "provenance": (
            "Locally authored synthetic examples only; no external repositories or credentials."
        ),
        "license": "MIT",
        "label_policy": (
            "1 = invented credential shape; 0 = benign template in its authored context."
        ),
        "limitations": [
            "Labels do not assert credential validity; no remote checks performed.",
            "Template review is local inspection, not independent human adjudication.",
            "Entire credential/negative families are held out; coverage differs by split.",
            "Synthetic balanced data does not estimate real-world precision or prevalence.",
            "Metadata must not be used as model features; no model is trained in sprint 2.",
        ],
    }
    return data, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--per-family", type=int, default=DEFAULT_PER_FAMILY)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    try:
        data, manifest = build(args.per_family, args.seed)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "dataset.csv").write_bytes(data)
        (args.output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except (ValueError, OSError):
        # Never echo paths, row contents, or exception messages into logs.
        parser.exit(
            2, "Dataset build failed: check counts, group integrity, and output permissions.\n"
        )
    print(f"Built {manifest['rows']} synthetic examples; label counts: {manifest['label_counts']}.")
    print(f"Dataset SHA-256: {manifest['dataset_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
