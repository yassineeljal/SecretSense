"""Shared scanner API. Findings never retain raw matched values."""

from bisect import bisect_right
from dataclasses import asdict, dataclass, field
from pathlib import Path

from secretsense.model.predict import LocalPredictor, PredictionError
from secretsense.remediation import Playbook, get_playbook
from secretsense.scanner.candidates import extract_candidates
from secretsense.scanner.walker import WalkState, read_text, walk_files


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    column: int
    rule_id: str
    service: str
    severity: str
    masked_value: str
    explanation: str
    model_score: float | None = None
    model_decision: str | None = None
    remediation: Playbook | None = None
    commit: str | None = None
    blob: str | None = None


@dataclass
class ScanReport:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    entries_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    engine: str = "rules-and-entropy"
    model: dict | None = None
    history: dict | None = None

    @property
    def complete(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {"schema_version": "1.2", **asdict(self), "complete": self.complete}


def mask_value(value: str) -> str:
    return "[REDACTED]" if len(value) < 12 else f"{value[:4]}…{value[-4:]}"


def scan_text(
    content: str, filename: str = "<text>", *, predictor: LocalPredictor | None = None
) -> list[Finding]:
    """Detect locally and optionally annotate all candidates with uncalibrated scores.

    Prediction errors raise a value-free PredictionError. scan_path handles them
    by preserving unscored findings and marking the report incomplete.
    """
    findings: list[Finding] = []
    line_starts = [0] + [index + 1 for index, char in enumerate(content) if char == "\n"]
    candidates = extract_candidates(content)
    scores = predictor.score(content, candidates) if predictor else [None] * len(candidates)
    for candidate, score in zip(candidates, scores, strict=True):
        line = bisect_right(line_starts, candidate.start)
        value = content[candidate.start : candidate.end]
        findings.append(
            Finding(
                filename,
                line,
                candidate.start - line_starts[line - 1] + 1,
                candidate.rule_id,
                candidate.service,
                candidate.severity,
                "[REDACTED]" if candidate.rule_id == "private-key" else mask_value(value),
                candidate.explanation,
                score,
                ("above-threshold" if score >= predictor.threshold else "below-threshold")
                if score is not None
                else None,
                get_playbook(candidate.service),
            )
        )
    return sorted(findings, key=lambda finding: (finding.line, finding.column, finding.rule_id))


def scan_path(
    path: str | Path,
    *,
    max_bytes: int = 1_048_576,
    max_files: int = 10_000,
    predictor: LocalPredictor | None = None,
) -> ScanReport:
    """Scan a local target; byte limits apply per file, entry limits to traversal."""
    if max_bytes < 1 or max_files < 1:
        raise ValueError("Scan limits must be positive integers.")
    root = Path(path).absolute()
    state = WalkState()
    report = new_report(predictor)
    for file in walk_files(root, state, max_files):
        try:
            content = read_text(file, max_bytes)
        except OSError:
            state.errors.append("Unable to read a file; the scan is incomplete.")
            continue
        if content is None:
            state.skipped += 1
            continue
        filename = file.relative_to(root).as_posix() if file != root else file.name
        try:
            findings = scan_text(content, filename, predictor=predictor)
        except PredictionError:
            state.errors.append("Local model prediction failed; some findings remain unscored.")
            findings = scan_text(content, filename)
        report.findings.extend(findings)
        report.files_scanned += 1
    report.findings.sort(key=lambda finding: (finding.path, finding.line, finding.column))
    report.entries_skipped = state.skipped
    report.errors = list(dict.fromkeys(state.errors))
    return report


def new_report(predictor: LocalPredictor | None = None) -> ScanReport:
    """Shared provenance for working-tree and history scans."""
    return ScanReport(
        engine="rules-and-entropy+local-ml" if predictor else "rules-and-entropy",
        model={
            "sha256": predictor.sha256,
            "threshold": predictor.threshold,
            "score_kind": "uncalibrated-positive-class-score",
            "policy": "annotate-all-candidates",
        }
        if predictor
        else None,
    )
