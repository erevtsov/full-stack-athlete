"""hybrid-athlete CLI — placeholder entry point."""

from __future__ import annotations

import typer

from hybrid_athlete import __version__

app = typer.Typer()


@app.command()
def version() -> None:
    """Print the installed package version."""
    typer.echo(__version__)
