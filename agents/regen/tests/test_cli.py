"""Tests for the Regen CLI (help + config-error paths, no network)."""

from __future__ import annotations

from typer.testing import CliRunner

from regen.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "regen" in result.output.lower()


def test_cli_incidents_help():
    result = runner.invoke(app, ["incidents", "--help"])
    assert result.exit_code == 0


def test_cli_incident_help():
    result = runner.invoke(app, ["incident", "--help"])
    assert result.exit_code == 0


def test_cli_alerts_help():
    result = runner.invoke(app, ["alerts", "--help"])
    assert result.exit_code == 0


def test_cli_correlate_help():
    result = runner.invoke(app, ["correlate", "--help"])
    assert result.exit_code == 0


def test_cli_serve_help():
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0


def test_cli_incidents_without_base_url_errors(monkeypatch):
    monkeypatch.delenv("REGEN_BASE_URL", raising=False)
    result = runner.invoke(app, ["incidents"])
    assert result.exit_code == 1
    assert "REGEN_BASE_URL" in result.output


def test_cli_correlate_without_base_url_errors(monkeypatch):
    monkeypatch.delenv("REGEN_BASE_URL", raising=False)
    result = runner.invoke(app, ["correlate", "42"])
    assert result.exit_code == 1
    assert "REGEN_BASE_URL" in result.output
