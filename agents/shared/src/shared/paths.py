"""Standard XDG data paths for agent alert logs."""

from __future__ import annotations

from pathlib import Path


def agent_data_dir(agent_name: str) -> Path:
    """Return ``~/.local/share/<agent_name>``."""
    return Path.home() / ".local" / "share" / agent_name


def agent_alert_log(agent_name: str) -> Path:
    """Return ``~/.local/share/<agent_name>/alerts.jsonl``."""
    return agent_data_dir(agent_name) / "alerts.jsonl"
