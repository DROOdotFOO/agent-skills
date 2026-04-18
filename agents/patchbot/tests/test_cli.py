"""Tests for the patchbot CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from patchbot.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "dependency" in result.output.lower()


def test_cli_scan_help():
    result = runner.invoke(app, ["scan", "--help"])
    assert result.exit_code == 0


def test_cli_serve_help():
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0


def test_cli_update_help():
    result = runner.invoke(app, ["update", "--help"])
    assert result.exit_code == 0
