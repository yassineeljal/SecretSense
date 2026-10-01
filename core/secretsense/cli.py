"""Command-line entry point and explicit CI exit codes."""

from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from secretsense.model.predict import LocalPredictor
from secretsense.report.console import render_console
from secretsense.report.html_report import render_html
from secretsense.report.json_report import render_json
from secretsense.report.sarif import render_sarif
from secretsense.scanner.engine import scan_path
from secretsense.scanner.history import scan_history

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)


class OutputFormat(StrEnum):
    console = "console"
    json = "json"
    html = "html"
    sarif = "sarif"


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
    history: Annotated[bool, typer.Option(help="Scan local Git history from --ref.")] = False,
    ref: Annotated[str, typer.Option(help="Local Git revision for history scanning.")] = "HEAD",
    max_commits: Annotated[int, typer.Option(min=1)] = 100,
    max_total_bytes: Annotated[int, typer.Option(min=1)] = 52_428_800,
    timeout: Annotated[float, typer.Option(min=0.1, help="History deadline in seconds.")] = 30,
    model: Annotated[
        Path | None, typer.Option(help="Trusted local model pickle; enables score annotations.")
    ] = None,
    model_sha256: Annotated[
        str | None, typer.Option(help="SHA-256 from independently trusted training metadata.")
    ] = None,
):
    """Scan UTF-8 files using credential patterns and assignment entropy."""
    try:
        if (model is None) != (model_sha256 is None):
            raise ValueError("Provide both --model and --model-sha256 to enable local ML.")
        predictor = (
            LocalPredictor.load(model, expected_sha256=model_sha256) if model is not None else None
        )
        report = (
            scan_history(
                path,
                ref=ref,
                max_commits=max_commits,
                max_bytes=max_bytes,
                max_files=max_files,
                max_total_bytes=max_total_bytes,
                timeout=timeout,
                predictor=predictor,
            )
            if history
            else scan_path(path, max_bytes=max_bytes, max_files=max_files, predictor=predictor)
        )
    except (ValueError, OSError) as error:
        message = str(error) if isinstance(error, ValueError) else "Unable to access scan target."
        typer.echo(f"Error: {message}", err=True)
        raise typer.Exit(2) from None
    renderer = {
        OutputFormat.console: render_console,
        OutputFormat.json: render_json,
        OutputFormat.html: render_html,
        OutputFormat.sarif: render_sarif,
    }[format]
    typer.echo(renderer(report))
    raise typer.Exit(2 if not report.complete else int(bool(report.findings)))
