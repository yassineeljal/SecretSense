"""Command-line entry point and explicit CI exit codes."""

from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from secretsense.report.console import render_console
from secretsense.report.json_report import render_json
from secretsense.scanner.engine import scan_path

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)


class OutputFormat(StrEnum):
    console = "console"
    json = "json"


@app.callback()
def main():
    """Find potential secrets locally. Reports always mask detected values."""


@app.command()
def scan(
    path: Annotated[Path, typer.Argument(help="Local file or directory to scan.")],
    format: Annotated[OutputFormat, typer.Option("--format", "-f")] = OutputFormat.console,
    max_bytes: Annotated[int, typer.Option(min=1, help="Maximum bytes per file.")] = 1_048_576,
    max_files: Annotated[
        int, typer.Option(min=1, help="Maximum directory entries visited.")
    ] = 10_000,
):
    """Scan UTF-8 files using credential patterns and assignment entropy."""
    try:
        report = scan_path(path, max_bytes=max_bytes, max_files=max_files)
    except (ValueError, OSError) as error:
        message = str(error) if isinstance(error, ValueError) else "Unable to access scan target."
        typer.echo(f"Error: {message}", err=True)
        raise typer.Exit(2) from None
    typer.echo(render_json(report) if format == OutputFormat.json else render_console(report))
    raise typer.Exit(2 if not report.complete else int(bool(report.findings)))
