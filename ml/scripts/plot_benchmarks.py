"""Export comparison figures from aggregate metrics; no dataset or model is loaded."""

import argparse
import json
from pathlib import Path

from ml.scripts.build_dataset import ROOT

METHODS = {
    "regex_only": "Regex",
    "rules_and_entropy": "Rules + entropy\n(default and ML annotations)",
    "annotated_value_model": "ML annotated values\n(hypothetical filter)",
    "candidate_pipeline_model": "ML scanner candidates\n(hypothetical filter)",
}


def render(report_path: Path, output_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    report = json.loads(report_path.read_text(encoding="utf-8"))
    measured = report["evaluation"]["test"]["metrics"]
    rows = measured["rules_and_entropy"]["rows"]
    threshold = report["selection"]["selected"]["threshold"]
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    with plt.rc_context({"font.size": 10, "svg.fonttype": "none", "svg.hashsalt": "secretsense"}):
        fig, ax = plt.subplots(figsize=(12, 6), layout="constrained")
        x = np.arange(len(METHODS))
        for offset, (key, color) in enumerate(
            zip(("precision", "recall", "f1"), ("#166b8a", "#b65719", "#4e477d"), strict=True)
        ):
            bars = ax.bar(
                x + (offset - 1) * 0.24,
                [measured[name][key] * 100 for name in METHODS],
                0.24,
                label=key.capitalize() if key != "f1" else "F1",
                color=color,
            )
            ax.bar_label(bars, fmt="%.1f", fontsize=9, padding=3)
        ax.set_xticks(x, list(METHODS.values()))
        ax.set_ylim(0, 116)
        ax.set_yticks(range(0, 101, 20))
        ax.set_ylabel("Score (%)")
        ax.set_title(
            f"SecretSense · synthetic grouped holdout ({rows:,} rows)\n"
            f"Frozen model threshold {threshold:g}; no real-world accuracy claim",
            pad=20,
        )
        ax.legend(loc="upper center", ncols=3, frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
        for suffix in ("svg", "png"):
            path = output_dir / f"quality-comparison.{suffix}"
            fig.savefig(path, dpi=160, metadata={"Date": None} if suffix == "svg" else {})
            outputs.append(path)
        plt.close(fig)

        fig, axes = plt.subplots(1, 2, figsize=(10, 5), layout="constrained")
        maximum = max(
            max(row)
            for name in ("rules_and_entropy", "candidate_pipeline_model")
            for row in measured[name]["confusion_matrix"]
        )
        for ax, name in zip(axes, ("rules_and_entropy", "candidate_pipeline_model"), strict=True):
            matrix = measured[name]["confusion_matrix"]
            ax.imshow(matrix, cmap="Blues", vmin=0, vmax=maximum)
            for i in range(2):
                for j in range(2):
                    value = matrix[i][j]
                    ax.text(
                        j,
                        i,
                        str(value),
                        ha="center",
                        va="center",
                        fontsize=20,
                        color="white" if value > maximum * 0.55 else "#172b3a",
                    )
            ax.set_xticks([0, 1], ["Negative", "Positive"])
            ax.set_yticks([0, 1], ["Negative", "Positive"])
            ax.set_xlabel("Predicted class")
            ax.set_ylabel("Authored synthetic label")
            ax.set_title(METHODS[name])
        fig.suptitle(
            f"Synthetic test confusion matrices · {rows:,} rows\n"
            "ML annotations preserve the default scanner's findings",
            fontsize=13,
        )
        for suffix in ("svg", "png"):
            path = output_dir / f"confusion-matrices.{suffix}"
            fig.savefig(path, dpi=160, metadata={"Date": None} if suffix == "svg" else {})
            outputs.append(path)
        plt.close(fig)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=ROOT / "results" / "baseline.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "figures")
    args = parser.parse_args()
    try:
        outputs = render(args.report, args.output_dir)
    except Exception:
        parser.exit(
            2, "Figure export failed; check aggregate report, plots extra, and output directory.\n"
        )
    print(f"Exported {len(outputs)} aggregate benchmark figures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
