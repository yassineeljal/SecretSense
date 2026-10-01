# CLI and library usage

Install from the checkout with `python -m pip install -e './core[dev]'`.
The package has not been published to PyPI.

```sh
secretsense scan ./my-project
secretsense scan ./my-project --format json
secretsense scan ./my-project --max-bytes 2097152 --max-files 20000
secretsense scan ./my-project/.env
python -m secretsense scan ./my-project
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--format`, `-f` | `console` | `console`, `json`, `html`, or `sarif` |
| `--model` | Disabled | Trusted local model pickle; annotates every candidate |
| `--model-sha256` | None | Required with `--model`; digest from independently trusted metadata |
| `--max-bytes` | `1048576` | Maximum bytes read per file; larger files are skipped |
| `--max-files` | `10000` | Maximum directory entries visited, including ignored entries and directories |

Nested `.gitignore` files apply within the scan root. Later patterns and nested
rules can override earlier patterns, but excluded parent directories are never
entered. Ancestor `.gitignore` files outside the target, global Git exclusions,
and `.git/info/exclude` are not read. Tracked files are not treated specially.
An explicit file target is scanned even if a surrounding `.gitignore` excludes it;
this is useful for checking local `.env` files.

Built-in directory exclusions: `.git`, `node_modules`, `.venv`, `venv`,
`__pycache__`, `.next`, `.pytest_cache`, `.ruff_cache`, `dist`, `build`, `vendor`.
Symlinks and special files are skipped. Only UTF-8 text is scanned; NUL-containing,
invalid UTF-8, and oversized files are skipped. Traversal beyond 128 directory
levels and `.gitignore` files over 1 MiB produce incomplete-scan errors.

| Exit code | Meaning |
| --- | --- |
| `0` | No candidates in the files actually scanned |
| `1` | At least one candidate |
| `2` | Invalid arguments, unreadable input, or a traversal/configuration limit |

Incomplete scans take precedence over candidate exit codes. JSON reports contain
`schema_version` (now `1.2`), `engine`, `findings`, `files_scanned`, `entries_skipped`,
`errors`, `model`, `history`, and `complete`. `complete` means no processing error occurred within the chosen
scope; intentionally skipped files remain excluded. Invalid CLI arguments or a
missing target produce an error on stderr, not a JSON report.

Findings have relative paths, one-based line and character column numbers, a rule
ID, service, severity, masked value, explanation, `model_score`, and `model_decision`.
The two model fields are null when scoring is disabled or fails. Reports go to
stdout; use shell redirection to save them outside the scanned directory so the
report cannot become scan input. Filenames are escaped for terminal output but
are not treated as secret-bearing input.

```sh
secretsense scan ./my-project --format html > ../scan-report.html
```

HTML reports contain an accessible findings table, scan completeness, skipped
counts, errors, and score explanations. They escape all dynamic text, include a
restrictive Content Security Policy, and load no scripts or remote assets.

## Optional local model annotations

Install `python -m pip install -e './core[ml]'` and use the matching training
environment documented in the [model card](model-card.md). A model is never
bundled, downloaded, or discovered automatically. This example uses the existing
local sprint 3 artifact and its recorded digest:

```sh
secretsense scan ./my-project --format json \
  --model ml/results/baseline.pkl \
  --model-sha256 45b4c1acdcb9e77bee8f6191b8926f7573f40e30c2234f050ae4c40bcfa91084
```

Only use a pickle from a trusted local run and an independently trusted digest.
A checksum supplied by the same untrusted source as a pickle does not make it
safe. The loader checks regular-file access, the 32 MiB limit, the exact bytes'
SHA-256 before unpickling, feature schema, fitted forest input/class schema, and
finite threshold. On systems with `O_NOFOLLOW`, model symlinks are rejected.
Deserialization warnings, including version incompatibility, are errors with
value-free messages. Loading failure exits 2 before scanning; it never silently
falls back to an apparently successful rules scan.

| Field or behavior | Meaning |
| --- | --- |
| `model_score` | Uncalibrated positive-class forest score in [0, 1]; not credential validity |
| `model_decision` | `above-threshold` for score >= artifact threshold, otherwise `below-threshold` |
| Threshold | Frozen validation-selected artifact threshold; 0.6 for the recorded baseline |
| Severity | Unchanged rule-based review priority; independent of model score |
| Finding retention | Every rules/entropy candidate remains visible, including below-threshold ones |
| Exit codes | 1 for any candidate regardless of score; 2 takes precedence for incomplete scans |

Rules mode has `engine: "rules-and-entropy"` and `model: null`. ML mode uses
`engine: "rules-and-entropy+local-ml"`; `model` records `sha256`, `threshold`,
`score_kind: "uncalibrated-positive-class-score"`, and
`policy: "annotate-all-candidates"`. JSON retains full numeric scores; console and
HTML round display to four decimals. Decisions use the unrounded score.
Schema 1.1 introduced model fields; schema 1.2 adds history and remediation.
Strict consumers must accept the current version.

Scoring uses batches of at most 256 numeric vectors. Repeated identical values
use their own candidate offsets for context features. On inference failure, all
findings from that file are preserved unscored, an error is recorded, and the scan
continues with `complete: false` and exit 2. The proposed 0.4/0.8 confidence bands
remain deferred pending calibration. The measured recall regression rules out
using the current model to hide findings.

```python
from secretsense import scan_path, scan_text

report = scan_path("./my-project")
print(report.to_dict())
findings = scan_text('password = "your_password_here"', filename="example.py")
```

`scan_text` is an in-memory primitive with no input-size limit; future API callers
must enforce request limits before invoking it. The CLI's file limits do not apply
to this function.

To score through the library, explicitly construct the trusted predictor:

```python
from pathlib import Path
from secretsense.model.predict import LocalPredictor

predictor = LocalPredictor.load(
    Path("ml/results/baseline.pkl"),
    expected_sha256="45b4c1acdcb9e77bee8f6191b8926f7573f40e30c2234f050ae4c40bcfa91084",
)
report = scan_path("./my-project", predictor=predictor)
```

`scan_text(..., predictor=predictor)` raises a value-free `PredictionError` on
inference failure. `scan_path` implements the preservation/incomplete-report
policy described above. Direct predictor construction is intended for internal
use and testing; use `LocalPredictor.load` to validate real artifacts.

## Git history, remediation, and SARIF (sprint 5)

```sh
secretsense scan ./my-project --history --format json
secretsense scan ./my-project --history --ref HEAD --max-commits 500 --timeout 60
secretsense scan ./my-project --format sarif > ../scan.sarif
```

`--history` scans snapshots reachable from one local commit (default `--ref HEAD`).
The target must be the repository root or a bare repository. Git must be installed.
No checkout, diff/textconv, smudge filter, hook, submodule operation, or network
fetch is performed. Git configuration environment variables are stripped, system
and global configuration are disabled, and protocols/lazy fetching are disabled.
Tracked historical files are scanned even if `.gitignore` or directory exclusions
would hide them in a working-tree scan. Symlinks, submodules, binary, and non-UTF-8
blob contents are skipped. Non-UTF-8 paths produce an incomplete-scan error.

The scanner deduplicates `(path, blob ID)` pairs. Renames and distinct blob versions
remain separate; a repeated unchanged snapshot is scanned once. Each finding's
`commit` is the first encountered snapshot containing that blob, **not** necessarily
the introducing commit. `blob` contains its Git object ID. Neither commit messages
nor author identities enter reports. Uncommitted files, other branches not reachable
from `ref`, reflogs, unreachable objects, and Git LFS payloads are outside scope.
LFS pointer text may be scanned; objects are never fetched.

History defaults: 100 commits, 10,000 visited tree entries (including duplicate
snapshots), 1 MiB per blob, 50 MiB total blob reads (`--max-total-bytes`), 30 seconds
(`--timeout`), and an 8 MiB fixed cap per Git tree listing. Deadlines interrupt Git
I/O and are checked after Python analysis of each bounded blob; an individual
scanner/model call is not forcibly interrupted. Traversal caps, oversized blobs,
missing objects, shallow history, and Git failures preserve available findings and
produce `complete: false` / exit 2. Intentional binary/symlink exclusions are counted
as skipped and do not themselves make a scan incomplete.

```python
from secretsense import scan_history
report = scan_history("./my-project", max_commits=500, timeout=60)
```

JSON **schema 1.2** adds `history` scan metadata and `remediation`, `commit`, and
`blob` finding fields to schema 1.1. Working-tree history/commit/blob fields are null.
Remediation contains a title and static steps covering all services plus a generic
fallback. [Playbooks](remediation.md) guide local triage and revocation without
performing any changes. Console/HTML display guidance and historical commit IDs.

`--format sarif` emits SARIF 2.1.0 rule help, one-based Unicode character locations,
severity, model annotations, history properties, and processing errors through
`invocations[].executionSuccessful` and notifications. Findings remain masked;
SARIF uses `[REDACTED]` and includes no snippets or source-content hashes. URIs are
percent-encoded paths relative to the scan root. Fingerprints use only metadata
and are not stable when line numbers move. The [GitHub Action](github-action.md)
converts paths to workspace-relative locations and leaves upload to the caller.
