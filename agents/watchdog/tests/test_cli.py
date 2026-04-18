"""Tests for the watchdog CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from watchdog.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "health monitor" in result.output.lower()


def test_cli_scan_help():
    result = runner.invoke(app, ["scan", "--help"])
    assert result.exit_code == 0


def test_cli_serve_help():
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0


def test_cli_alerts_help():
    result = runner.invoke(app, ["alerts", "--help"])
    assert result.exit_code == 0
