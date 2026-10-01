"""Opt-in local scoring; scores never suppress scanner findings."""

import math
import warnings
from dataclasses import dataclass, field
from pathlib import Path

from secretsense.features import extract_features
from secretsense.model.artifact import load_trusted_artifact
from secretsense.scanner.candidates import Candidate


class PredictionError(ValueError):
    """A value-free inference failure that makes a file scan incomplete."""


@dataclass(frozen=True)
class LocalPredictor:
    model: object = field(repr=False)
    threshold: float
    sha256: str

    @classmethod
    def load(cls, path: Path, *, expected_sha256: str) -> "LocalPredictor":
        payload = load_trusted_artifact(path, expected_sha256=expected_sha256)
        return cls(payload["model"], float(payload["threshold"]), expected_sha256)

    def score(self, content: str, candidates: list[Candidate]) -> list[float]:
        """Bound prediction batches; retain numeric scores only after inference."""
        scores = []
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                for start in range(0, len(candidates), 256):
                    batch = candidates[start : start + 256]
                    vectors = [
                        extract_features(
                            content[item.start : item.end], content, value_start=item.start
                        )
                        for item in batch
                    ]
                    probabilities = self.model.predict_proba(vectors)
                    if len(probabilities) != len(batch):
                        raise ValueError
                    for row in probabilities:
                        if len(row) != 2:
                            raise ValueError
                        negative, positive = map(float, row)
                        if not all(
                            math.isfinite(x) and 0 <= x <= 1 for x in (negative, positive)
                        ) or not math.isclose(negative + positive, 1, abs_tol=1e-6):
                            raise ValueError
                        scores.append(positive)
        except Exception:
            raise PredictionError(
                "Local model prediction failed; findings remain unscored."
            ) from None
        return scores
