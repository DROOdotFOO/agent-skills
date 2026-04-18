"""Tests for the digest CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from digest.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "digest" in result.output.lower()


def test_cli_generate_help():
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0


def test_cli_serve_help():
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0


def test_cli_alerts_help():
    result = runner.invoke(app, ["alerts", "--help"])
    assert result.exit_code == 0
