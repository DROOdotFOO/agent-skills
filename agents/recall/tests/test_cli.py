"""Tests for the recall CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from recall.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "knowledge capture" in result.output.lower()


def test_cli_serve_help():
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0


def test_cli_stats(tmp_path: Path):
    db = tmp_path / "recall.db"
    result = runner.invoke(app, ["stats", "--db", str(db)])
    assert result.exit_code == 0
    assert "0" in result.output  # empty db has 0 entries


def test_cli_search_empty(tmp_path: Path):
    db = tmp_path / "recall.db"
    result = runner.invoke(app, ["search", "anything", "--db", str(db)])
    assert result.exit_code == 0


def test_cli_add_and_list(tmp_path: Path):
    db = tmp_path / "recall.db"
    result = runner.invoke(
        app,
        ["add", "test insight content here", "--type", "insight", "--db", str(db)],
    )
    assert result.exit_code == 0

    result = runner.invoke(app, ["list", "--db", str(db)])
    assert result.exit_code == 0
    assert "insight" in result.output
