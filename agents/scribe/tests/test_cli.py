"""Tests for the scribe CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from scribe.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Session insight extractor" in result.output


def test_cli_analyze_requires_project():
    result = runner.invoke(app, ["analyze", "sess-001"])
    assert result.exit_code == 1


def test_cli_analyze_missing_session(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "analyze",
            "nonexistent",
            "--project",
            "/fake/path",
        ],
    )
    assert result.exit_code == 1
    assert "No session data" in result.output


def test_cli_analyze_dry_run(sample_session: tuple[str, str, Path], monkeypatch):
    session_id, project_path, claude_dir = sample_session

    # Monkeypatch CLAUDE_DIR so parse_session finds our fixture
    import scribe.session_parser as sp

    monkeypatch.setattr(sp, "CLAUDE_DIR", claude_dir)

    result = runner.invoke(
        app,
        [
            "analyze",
            session_id,
            "--project",
            project_path,
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "insight(s) extracted" in result.output


def test_cli_stats_no_log():
    result = runner.invoke(app, ["stats"])
    # Should handle missing log gracefully
    assert result.exit_code == 0


def test_cli_recent_no_log():
    result = runner.invoke(app, ["recent"])
    assert result.exit_code == 0


def test_cli_watch_once(
    sample_session: tuple[str, str, Path],
    sample_history: Path,
    tmp_path: Path,
    monkeypatch,
):
    session_id, project_path, claude_dir = sample_session

    # Monkeypatch paths
    import scribe.watcher as w

    monkeypatch.setattr(w, "OFFSETS_PATH", tmp_path / "offsets.json")
    monkeypatch.setattr(w, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(w, "ACTIVITY_LOG", tmp_path / "activity.jsonl")

    result = runner.invoke(
        app,
        [
            "watch",
            "--once",
            "--idle-minutes",
            "0",
            "--db",
            str(tmp_path / "recall.db"),
        ],
        env={"CLAUDE_DIR": str(claude_dir)},
    )

    # May not find sessions without proper history path wiring,
    # but should not crash
    assert result.exit_code == 0
