"""Tests for the autoresearch CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from autoresearch.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "experiment" in result.output.lower()


def test_cli_init_help():
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0


def test_cli_serve_help():
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0


def test_cli_dashboard_help():
    result = runner.invoke(app, ["dashboard", "--help"])
    assert result.exit_code == 0


def test_cli_status_help():
    result = runner.invoke(app, ["status", "--help"])
    assert result.exit_code == 0
