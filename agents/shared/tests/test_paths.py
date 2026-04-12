"""Tests for shared.paths."""

from pathlib import Path

from shared.paths import agent_alert_log, agent_data_dir


def test_agent_data_dir_uses_home():
    result = agent_data_dir("sentinel")
    assert result == Path.home() / ".local" / "share" / "sentinel"


def test_agent_alert_log_appends_filename():
    result = agent_alert_log("watchdog")
    assert result == Path.home() / ".local" / "share" / "watchdog" / "alerts.jsonl"


def test_agent_data_dir_accepts_any_name():
    result = agent_data_dir("my-custom-agent")
    assert result.name == "my-custom-agent"
    assert result.parent == Path.home() / ".local" / "share"
