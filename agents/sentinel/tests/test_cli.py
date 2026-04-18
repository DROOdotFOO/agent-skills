"""Tests for the sentinel CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from sentinel.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "sentinel" in result.output.lower()


def test_cli_check_help():
    result = runner.invoke(app, ["check", "--help"])
    assert result.exit_code == 0


def test_cli_serve_help():
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0


def test_cli_alerts_help():
    result = runner.invoke(app, ["alerts", "--help"])
    assert result.exit_code == 0
