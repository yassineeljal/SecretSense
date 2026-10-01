"""Exercise dataset contracts using values assembled only at runtime."""

import csv
import hashlib
import io
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import replace

import pytest

from ml.scripts.build_dataset import ROOT, assign_splits, build, clean, validate_rows
from ml.scripts.collect_false_positives import collect
from ml.scripts.generate_fake_secrets import generate


@pytest.fixture(scope="module")
def dataset():
    return build()


def read_rows(data):
    return list(csv.DictReader(io.StringIO(data.decode())))


def test_default_size_balance_and_isolation(dataset):
    data, manifest = dataset
    rows = read_rows(data)
    validate_rows(rows)
    assert len(rows) == 6000
    assert Counter(row["label"] for row in rows) == {"0": 3000, "1": 3000}
    assert manifest["duplicates_removed"] == 0
    assert manifest["dataset_sha256"] == hashlib.sha256(data).hexdigest()
    assert {name: stats["rows"] for name, stats in manifest["splits"].items()} == {
        "train": 3600,
        "validation": 1200,
        "test": 1200,
    }
    memberships = defaultdict(set)
    for row in rows:
        for column in ("template_family", "source_group", "value"):
            memberships[column, row[column]].add(row["split"])
    assert all(len(splits) == 1 for splits in memberships.values())
    assert len({row["sample_id"] for row in rows}) == 6000
    for stats in manifest["splits"].values():
        assert stats["label_counts"]["0"] == stats["label_counts"]["1"]


def test_byte_reproducibility_and_seed_variation(dataset):
    data, manifest = dataset
    repeated, repeated_manifest = build()
    assert hashlib.sha256(data).digest() == hashlib.sha256(repeated).digest()
    assert manifest == repeated_manifest
    other, _ = build(seed=1234)
    assert hashlib.sha256(data).digest() != hashlib.sha256(other).digest()


def test_provenance_and_safe_representations(dataset):
    data, manifest = dataset
    summary = json.dumps(manifest)
    examples = generate(2) + collect(2)
    for example in examples:
        assert example.value not in repr(example)
        assert example.text not in repr(example)
        assert example.license == "MIT"
        assert example.source_id and example.review_status
    assert all(row["value"] not in summary for row in read_rows(data))
    for source in manifest["sources"]:
        assert hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]


def test_normalization_deduplication_and_conflict_privacy():
    example = generate(1)[0]
    padded = replace(example, text="\r\n" + example.text + "\r\n", value=" " + example.value + " ")
    examples, removed = clean([example, padded])
    assert len(examples) == 1 and removed == 1
    for conflict in (
        replace(example, label=0),
        replace(example, source_group="different-source"),
        replace(example, template_family="different-family"),
    ):
        with pytest.raises(ValueError) as error:
            clean([example, conflict])
        assert example.value not in str(error.value)
        assert example.text not in str(error.value)
    with pytest.raises(ValueError, match="Invalid dataset example"):
        clean([replace(example, label=2)])


def test_transitive_grouping_and_order_independence():
    examples = generate(2) + collect(2)
    # Bridge two existing families through one source, then a third family
    # through a different source. All three must stay in one split.
    examples[2] = replace(examples[2], source_group=examples[0].source_group)
    examples[4] = replace(examples[4], source_group=examples[3].source_group)
    split = assign_splits(examples, 42)
    assert len({split[example.sample_id] for example in examples[:6]}) == 1
    assert split == assign_splits(list(reversed(examples)), 42)


def test_insufficient_independent_groups_fail():
    examples = [replace(example, source_group="one-source") for example in generate(1) + collect(1)]
    with pytest.raises(ValueError, match="Not enough independent groups"):
        assign_splits(examples, 42)


def test_csv_validation_rejects_corruption(dataset):
    rows = read_rows(dataset[0])
    row = rows[0]
    variants = [
        [*rows, row],
        [{**row, "sample_id": "incorrect"}, *rows[1:]],
        [{**row, "label": "2"}, *rows[1:]],
        [{**row, "split": "unknown"}, *rows[1:]],
        [{**row, "value": ""}, *rows[1:]],
        [{**row, "split": "test" if row["split"] != "test" else "train"}, *rows[1:]],
        [{**row, "source_group": ""}, *rows[1:]],
        rows[1:],
    ]
    for variant in variants:
        with pytest.raises(ValueError) as error:
            validate_rows(variant)
        assert row["value"] not in str(error.value)


@pytest.mark.parametrize("count", [0, -1, 1001])
def test_invalid_counts(count):
    with pytest.raises(ValueError, match="between 1 and 1000"):
        build(count=count)


def test_cli_and_notebook(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "ml.scripts.build_dataset", "--output-dir", str(tmp_path)],
        cwd=ROOT.parent,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0
    data = (tmp_path / "dataset.csv").read_bytes()
    assert all(row["value"] not in result.stdout + result.stderr for row in read_rows(data))
    notebook = json.loads((ROOT / "notebooks" / "01_exploration.ipynb").read_text())
    code = "\n".join(
        "".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"
    )
    runner = tmp_path / "explore.py"
    runner.write_text(code, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(runner)],
        cwd=ROOT.parent,
        env={
            **os.environ,
            "SECRETSENSE_DATA_DIR": str(tmp_path),
            "PYTHONPATH": str(ROOT.parent),
        },
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0
    assert "6000" in result.stdout
    assert all(row["value"] not in result.stdout + result.stderr for row in read_rows(data))
    invalid = subprocess.run(
        [sys.executable, "-m", "ml.scripts.build_dataset", "--per-family", "0"],
        cwd=ROOT.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    assert invalid.returncode == 2
    assert "Traceback" not in invalid.stderr
