# Architecture

SecretSense is planned as a monorepo with one Python engine shared by a CLI, a
FastAPI service, and a Next.js demonstration site.

```text
Local files → bounded walker → regex / entropy → redacted findings → console / JSON
                                              (current implementation)

Candidates → features → local ML → decision → remediation → richer reports
                         (planned)
```

The current implementation lives in `core/secretsense/`: `scanner/walker.py`
handles input scope, `scanner/patterns.py` defines rules, `scanner/entropy.py`
calculates entropy, and `scanner/engine.py` creates findings. `report/` serializes
those findings and `cli.py` handles arguments and exit codes. `scan_text` and
`scan_path` are the library entry points. Raw values are transient and never stored
in a finding; there are no source snippets, credential checks, or network calls.

`pathspec.GitIgnoreSpec` provides pattern semantics; the walker applies each
directory's rules relative to that directory. See its
[API documentation](https://python-path-specification.readthedocs.io/en/latest/api.html).
The CLI uses [Typer command groups](https://typer.tiangolo.com/tutorial/commands/callback/).
CI uses a Python matrix following the
[GitHub Actions Python guide](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).

The next stages add `features/`, `model/`, `remediation/`, and optionally `llm/` to
the library. `ml/` will hold synthetic-data generation, dataset construction, and
evaluation notebooks. `api/` and `web/` will use the same scanner after enforcing
their own request limits. Empty application scaffolds are intentionally deferred
until their implementation sprint. See [the roadmap](roadmap.md).
