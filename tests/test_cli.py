from __future__ import annotations

from typer.testing import CliRunner

from hybrid_athlete.cli import app

runner = CliRunner()


def test_version_command_prints_version() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "0.1.0" in result.stdout
