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
| `--format`, `-f` | `console` | `console` or `json` |
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
`schema_version`, `engine`, `findings`, `files_scanned`, `entries_skipped`, `errors`,
and `complete`. `complete` means no processing error occurred within the chosen
scope; intentionally skipped files remain excluded. Invalid CLI arguments or a
missing target produce an error on stderr, not a JSON report.

Findings have relative paths, one-based line and character column numbers, a rule
ID, service, severity, masked value, and explanation. There are no ML probabilities
yet. Reports go to stdout; use shell redirection if you want to save them. Filenames
are escaped for terminal output but are not treated as secret-bearing input.

```python
from secretsense import scan_path, scan_text

report = scan_path("./my-project")
print(report.to_dict())
findings = scan_text('password = "your_password_here"', filename="example.py")
```

`scan_text` is an in-memory primitive with no input-size limit; future API callers
must enforce request limits before invoking it. The CLI's file limits do not apply
to this function.
