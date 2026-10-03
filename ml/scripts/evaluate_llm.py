"""Fresh synthetic experiment for the optional Ollama review. Reports contain aggregates only."""

import argparse
import json
import platform
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from secretsense.llm import AdvisorError, OllamaAdvisor, build_prompt
from secretsense.scanner.candidates import extract_candidates

from ml.scripts.common import family_rng, random_text

SEED = 20261101
GROUPS = ("deploy-yaml", "env-settings", "python-settings")
NEGATIVE_KINDS = ("cue-name", "placeholder-value", "no-cue")
POSITIVE_NAMES = {
    "deploy-yaml": ("client_secret", "webhook_secret", "signing_secret"),
    "env-settings": ("INTEGRATION_SECRET", "SERVICE_PASSWORD", "AUTH_TOKEN"),
    "python-settings": ("WEBHOOK_SIGNING_KEY", "api_secret", "db_password"),
}
CUE_NAMES = ("example", "fixture", "sample", "dummy")
PLACEHOLDER_WORDS = ("replace", "insert", "paste", "your", "change", "fill")


def render(group: str, name: str, value: str, comment: str = "") -> str:
    suffix = f"  # {comment}" if comment else ""
    if group == "deploy-yaml":
        return f'service:\n  {name}: "{value}"{suffix}\n'
    if group == "env-settings":
        return f'{name} = "{value}"{suffix}\n'
    return f'SETTINGS = {{"{name}": "{value}"}}{suffix}\n'


def generate(count: int = 60) -> list[dict]:
    if not 3 <= count <= 600 or count % 3:
        raise ValueError("Count must be a multiple of three between 3 and 600.")
    rows = []
    for group in GROUPS:
        rng = family_rng(SEED, "sprint8:" + group)
        names = POSITIVE_NAMES[group]
        for index in range(count):
            value = random_text(rng, rng.randint(32, 48))
            text = render(group, names[index % len(names)], value)
            rows.append(_row(group, 1, "positive", text, value))
        for index in range(count):
            kind = NEGATIVE_KINDS[index % 3]
            name = POSITIVE_NAMES[group][index % 3]
            cue = CUE_NAMES[(index // 3) % len(CUE_NAMES)]
            if kind == "cue-name":
                value = random_text(rng, rng.randint(32, 48))
                text = render(group, f"{cue}_{name}", value, f"{cue} only")
            elif kind == "placeholder-value":
                word = PLACEHOLDER_WORDS[(index // 3) % len(PLACEHOLDER_WORDS)]
                value = f"{word}_this_{random_text(rng, 8, 'abcdefghijklmnop')}_with_real_value"
                text = render(group, name, value)
            else:
                value = random_text(rng, rng.randint(32, 48))
                text = render(group, name, value)
            rows.append(_row(group, 0, kind, text, value))
    return rows


def _row(group, label, kind, text, value):
    return {"group": group, "label": label, "kind": kind, "text": text, "value": value}


def validate(rows: list[dict]) -> None:
    if len({row["value"] for row in rows}) != len(rows) or len(
        {row["text"] for row in rows}
    ) != len(rows):
        raise ValueError("Duplicate experiment input; content omitted.")


def review_rows(rows: list[dict], advisor: OllamaAdvisor) -> list[str]:
    outcomes = []
    for row in rows:
        text = row["text"]
        candidates = extract_candidates(text)
        targets = [item for item in candidates if advisor.reviews(item)]
        if not targets:
            outcomes.append("no-candidate")
            continue
        try:
            outcomes.append(advisor.review(build_prompt(text, candidates, targets[0])))
        except AdvisorError:
            outcomes.append("error")
    return outcomes


def rate(numerator: int, denominator: int):
    return round(numerator / denominator, 4) if denominator else None


def summarize(rows: list[dict], outcomes: list[str]) -> dict:
    reviewed = [(r, o) for r, o in zip(rows, outcomes, strict=True) if o in (
        "likely-secret", "likely-placeholder", "unsure")]
    candidates = [(r, o) for r, o in zip(rows, outcomes, strict=True) if o != "no-candidate"]

    def kept(pairs, drop):
        keep = [(r, o) for r, o in pairs if o not in drop]
        tp = sum(r["label"] for r, _ in keep)
        positives = sum(r["label"] for r, _ in pairs)
        return {
            "kept": len(keep),
            "precision": rate(tp, len(keep)),
            "recall": rate(tp, positives),
        }

    def breakdown(key):
        return {
            value: dict(Counter(o for r, o in zip(rows, outcomes, strict=True) if r[key] == value))
            for value in sorted({r[key] for r in rows})
        }

    return {
        "rows": len(rows),
        "rows_by_label": dict(Counter(r["label"] for r in rows)),
        "outcomes": dict(Counter(outcomes)),
        "candidate_coverage": {
            str(label): {
                "rows": sum(1 for r in rows if r["label"] == label),
                "with_candidate": sum(1 for r, _ in candidates if r["label"] == label),
            }
            for label in (0, 1)
        },
        "keep_everything": kept(candidates, set()),
        "drop_likely_placeholder": kept(reviewed, {"likely-placeholder"}),
        "drop_placeholder_and_unsure": kept(reviewed, {"likely-placeholder", "unsure"}),
        "by_kind": breakdown("kind"),
        "by_group": breakdown("group"),
        "errors": outcomes.count("error"),
    }


def run(output: Path, model: str, count: int, timeout: float) -> dict:
    rows = generate(count)
    validate(rows)
    advisor = OllamaAdvisor(model=model, timeout=timeout)
    started = time.perf_counter()
    outcomes = review_rows(rows, advisor)
    report = {
        "protocol": "docs/sprint8-llm-experiment.md",
        "seed": SEED,
        "model": model,
        "count_per_label_per_group": count,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "elapsed_seconds": round(time.perf_counter() - started, 1),
        "results": summarize(rows, outcomes),
        "limitations": "Synthetic data, one small model, one run; not real-repository evidence.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--output", type=Path, default=Path("ml/results/llm.json"))
    args = parser.parse_args()
    report = run(args.output, args.model, args.count, args.timeout)
    print(json.dumps(report["results"]["outcomes"], sort_keys=True))


if __name__ == "__main__":
    main()
