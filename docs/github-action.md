# Reusable GitHub Action

The root [action.yml](../action.yml) is a composite Action for Linux runners. It
installs Python 3.12 and the scanner from the Action's own `core/` in an isolated
environment, scans the caller's checkout locally, and writes redacted SARIF to
runner temporary storage. It does not execute source from the scan target, upload
results, fetch history, or validate credentials remotely. Installation downloads
Python/package dependencies; scanning itself stays local.

The Action is implemented and tested locally. It is not published to Marketplace
and no remote workflow success is claimed. In this checkout, use:

```yaml
name: Secret scan
on: [push, pull_request]
permissions:
  contents: read
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: ./
        id: secrets
        with:
          path: .
          history: 'false'
          fail-on-findings: 'true'
```

For another repository, once this code is available remotely, use
`yassineeljal/SecretSense@<reviewed-full-commit-sha>` instead of `./`. The placeholder
is deliberately not a release claim. Pin a reviewed commit. A local `./` Action
uses that checkout's code; do not run an untrusted PR's Action definition in a
privileged workflow or combine it with `pull_request_target` secrets.

| Input | Default | Meaning |
| --- | --- | --- |
| `path` | `.` | Workspace-relative file/directory; must resolve inside the workspace |
| `history` | `'false'` | Scan local history when `'true'`; target must be a repository root |
| `ref` | `HEAD` | One local revision; relevant only to history |
| `fail-on-findings` | `'true'` | Return failure for candidates; `'false'` still fails incomplete scans |
| `max-commits` | `'100'` | Maximum history commits; exceeding the cap marks the scan incomplete |
| `max-files` | `'10000'` | Visited directory/history entries |
| `max-bytes` | `'1048576'` | Per-file/blob bytes |
| `max-total-bytes` | `'52428800'` | Total history blob bytes |
| `timeout` | `'30'` | History deadline in seconds |

Boolean inputs accept exactly `'true'` or `'false'`. Values pass through environment
variables to Python; they are never interpolated into shell code. ML is disabled.
Outputs are `sarif` (absolute temporary report path) and `exit-code` (0 clean,
1 candidates, 2 invalid/incomplete). Outputs are set before a candidate/incomplete
failure. Limits use the CLI semantics described in [the usage guide](cli.md).

History requires a complete local clone. Set `fetch-depth: 0` in the caller's
checkout; a shallow clone produces exit 2. Increase `max-commits` deliberately for
larger repositories. Only ancestors of `ref` are included, not all branch tips,
reflogs, unreachable objects, or uncommitted files. Scan the working tree separately
when needed. Findings identify snapshots, not the introducing commits.

SARIF paths are relative to the workspace, including when scanning a subdirectory.
History findings can point to deleted files and old line numbers; use JSON/HTML for
historical investigation. SARIF metadata fingerprints use path/rule/location/commit,
not secret hashes, and change when locations move. There are no source snippets.
An upload step is intentionally left to the caller: uploading exposes redacted
findings and paths to GitHub, and GitHub can display source from its own checkout.
Review [GitHub SARIF support](https://docs.github.com/en/code-security/reference/code-scanning/sarif-support)
and your repository's code-scanning access/permissions before adding an uploader.
