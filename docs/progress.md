# Progress log

Every functional change must update this log and the relevant usage or design
documentation. Record actual validation separately from planned checks.

## 2026-09-30 — Foundations and first working scanner

### Delivered

- Created the Python package, Typer CLI, and importable `scan_text`/`scan_path` API.
- Added 15 service patterns, JWT and private-key-header detection, and entropy
  checks for literals assigned to secret-like names.
- Implemented nested `.gitignore` handling, built-in directory exclusions,
  bounded reads/traversal, symlink and special-file skipping, and incomplete-scan
  reporting. Bounded assignment-name matching avoids excessive regex work on
  repeated word boundaries.
- Added masked console and schema-versioned JSON reports, stable locations,
  explanations, and explicit exit codes. These two report formats were moved
  forward from sprint 4 to make the baseline usable and test its masking contract.
- Added MIT licensing, contribution/security policies, working agreements,
  architecture, usage, detection coverage, model-card and benchmark plans, and
  a threat model. Preserved the original project brief as an English roadmap.
- Configured GitHub Actions for Python 3.11–3.14, Ruff, pytest/coverage, builds,
  dependency auditing, Gitleaks, and Dependabot. Installed the local commit hook.
- Configured Gitleaks to scan the working directory, including untracked source.
  Its upstream hook otherwise scans only staged changes, which is insufficient
  in a fresh CI checkout. Excluded generated Python caches after runtime synthetic
  test tokens were correctly detected in bytecode and pytest node IDs; source
  test files remain covered.

### Validation

| Check | Local result |
| --- | --- |
| pytest on Python 3.11.16 | 46 passed |
| pytest on Python 3.12.13 | 46 passed; 97.65% statement coverage |
| pytest on Python 3.14.7 | 46 passed |
| Ruff lint and formatting | Passed |
| Source distribution and wheel build | Passed |
| `pip-audit --skip-editable` | No known vulnerabilities in installed dependencies; local editable package skipped |
| Gitleaks working-directory scan | No findings after generated-cache exclusions |
| Pre-commit across all tracked files | Gitleaks, Ruff lint, and Ruff formatting passed |
| Local documentation links and Git whitespace checks | Passed |
| CLI self-scan and `python -m secretsense` | Successful, no candidates in package source |

Regression coverage includes every detection rule, redaction in reports and object
representations, locations, duplicate suppression, placeholders, ignore anchoring
and negation, nested traversal limits, invalid/oversized ignore configuration,
binary/encoding/size exclusions, symlinks, named pipes, I/O errors, terminal filename
escaping, a long-input subprocess deadline, and CLI exit codes.

### Remaining work

Foundations and the classic scanner are implemented and validated locally. Remote
CI has not run on this change; Python 3.13 is configured in CI but was not tested
locally. This delivery remains local and has not been pushed, deployed, or published.

Next is sprint 2: reproducible synthetic data generation, reviewed negative
examples, provenance/grouped splits, at least 5,000 examples, and an exploration
notebook. ML inference, calibrated scores, HTML/SARIF, Git-history scanning,
remediation playbooks, API/site work, publication, and Ollama remain planned.
No model accuracy or benchmark result is claimed.
