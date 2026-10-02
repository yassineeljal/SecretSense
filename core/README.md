# SecretSense Python package

Local, offline secret detection for UTF-8 files. This first version uses service
patterns and assignment entropy by default. The optional `ml` extra enables trusted
local model annotations using `--model` and `--model-sha256`; scores never remove
findings. Console, JSON 1.2, self-contained HTML, and SARIF 2.1.0 reports are supported.
See the repository model card before using the synthetic baseline.

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

Sprint 5 adds `secretsense scan PATH --history`, `--format sarif`, service-specific
remediation in every format, and JSON schema 1.2 with history/commit/blob metadata.
History reads local objects with explicit bounds and never checks out source or
fetches remote objects. `from secretsense import scan_history` exposes the same
engine. See [CLI documentation](https://github.com/yassineeljal/SecretSense/blob/main/docs/cli.md), [playbooks](https://github.com/yassineeljal/SecretSense/blob/main/docs/remediation.md),
and the root [GitHub Action](https://github.com/yassineeljal/SecretSense/blob/main/docs/github-action.md). XGBoost is an optional
`experiments` dependency for offline comparison only; the CLI predictor is unchanged.


Sprint 6 adds an optional `api` dependency extra for the checkout's FastAPI service.
Install `./core[api]` and follow [the local API/site guide](https://github.com/yassineeljal/SecretSense/blob/main/docs/api-and-web.md).
The wheel still contains only the scanner; `api/` and the Next.js `web/` site run
from the repository. Web scanning keeps the rules/entropy default and fully
redacts values and filenames; no source is persisted or remotely verified.

The package metadata includes repository/documentation URLs and bundles the MIT
license. Version 0.1.0 remains unreleased. The repository's manual release workflow
defaults to building and validating artifacts; PyPI publication requires separately
configured ownership and trusted publishing. See the
[release guide](https://github.com/yassineeljal/SecretSense/blob/main/docs/release.md).
