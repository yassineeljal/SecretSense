"""Shared scanner API. Findings never retain raw matched values."""

from bisect import bisect_right
from dataclasses import asdict, dataclass, field
from pathlib import Path

from secretsense.scanner.entropy import shannon_entropy
from secretsense.scanner.patterns import ASSIGNMENT, RULES
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


@dataclass
class ScanReport:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    entries_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    engine: str = "rules-and-entropy"

    @property
    def complete(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {"schema_version": "1.0", **asdict(self), "complete": self.complete}


def mask_value(value: str) -> str:
    return "[REDACTED]" if len(value) < 12 else f"{value[:4]}…{value[-4:]}"


def scan_text(content: str, filename: str = "<text>") -> list[Finding]:
    """Detect format matches and high-entropy literals without network requests."""
    findings: list[Finding] = []
    occupied: list[tuple[int, int]] = []
    line_starts = [0] + [index + 1 for index, char in enumerate(content) if char == "\n"]

    def add(start: int, value: str, rule_id: str, service: str, severity: str, reason: str):
        line = bisect_right(line_starts, start)
        findings.append(
            Finding(
                filename,
                line,
                start - line_starts[line - 1] + 1,
                rule_id,
                service,
                severity,
                "[REDACTED]" if rule_id == "private-key" else mask_value(value),
                reason,
            )
        )

    for rule in RULES:
        for match in rule.pattern.finditer(content):
            occupied.append(match.span())
            add(
                match.start(),
                match.group(),
                rule.id,
                rule.service,
                rule.severity,
                "Matches a credential format; validity has not been checked.",
            )

    for match in ASSIGNMENT.finditer(content):
        start, end = match.span("value")
        value = match.group("value")
        if any(start < other_end and end > other_start for other_start, other_end in occupied):
            continue
        if value.lower().startswith(("your_", "example", "changeme", "placeholder", "process.env")):
            continue
        if value.startswith(("$", "os.getenv", "os.environ")):
            continue
        if shannon_entropy(value) >= 3.5:
            add(
                start,
                value,
                "generic-secret",
                "Generic",
                "medium",
                "High-entropy literal assigned to a secret-like name; review manually.",
            )
    return sorted(findings, key=lambda finding: (finding.line, finding.column, finding.rule_id))


def scan_path(
    path: str | Path, *, max_bytes: int = 1_048_576, max_files: int = 10_000
) -> ScanReport:
    """Scan a local target; byte limits apply per file, entry limits to traversal."""
    if max_bytes < 1 or max_files < 1:
        raise ValueError("Scan limits must be positive integers.")
    root = Path(path).absolute()
    state = WalkState()
    report = ScanReport()
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
        report.findings.extend(scan_text(content, filename))
        report.files_scanned += 1
    report.findings.sort(key=lambda finding: (finding.path, finding.line, finding.column))
    report.entries_skipped = state.skipped
    report.errors = list(dict.fromkeys(state.errors))
    return report
