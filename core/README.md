# SecretSense Python package

Local, offline secret detection for UTF-8 files. This first version uses service
patterns and assignment entropy; a trained machine-learning model is planned.

From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e './core[dev]'
secretsense scan ./core
secretsense scan ./core --format json
```

Reports contain masked values, never source snippets or complete detected values.
Exit codes: `0` no findings, `1` findings, `2` invalid input or incomplete scan.
See the repository's `docs/cli.md` and `docs/detection.md` for scope and limitations.
