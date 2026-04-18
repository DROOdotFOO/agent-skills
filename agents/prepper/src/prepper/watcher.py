"""Cross-agent alert watcher for prepper.

Polls JSONL alert logs from digest, sentinel, and watchdog. Aggregates
new entries into a unified log and dispatches macOS notifications.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from pydantic import BaseModel, Field
from shared.config import load_toml
from shared.notify import notify_macos
from shared.paths import agent_alert_log, agent_data_dir

# -- Config models -----------------------------------------------------------


class AgentLogConfig(BaseModel):
    """Pointer to one agent's JSONL alert log."""

    name: str
    path: Path


class NotificationConfig(BaseModel):
    """Notification dispatch settings."""

    macos: bool = True
    osascript: bool = True
    log_file: Path = Field(default_factory=lambda: agent_alert_log("prepper"))


class PrepperWatchConfig(BaseModel):
    """TOML-loadable config for ``prepper watch``."""

    poll_interval_minutes: int = 5
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    agent_logs: list[AgentLogConfig] = Field(default_factory=lambda: _default_agent_logs())

    @classmethod
    def from_toml(cls, path: Path) -> PrepperWatchConfig:
        data = load_toml(path)

        notif = data.get("notifications", {})
        logs_raw = data.get("agent_logs", [])

        agent_logs = [AgentLogConfig(name=e["name"], path=Path(e["path"])) for e in logs_raw]

        return cls(
            poll_interval_minutes=data.get("poll_interval_minutes", 5),
            notifications=NotificationConfig(**notif),
            agent_logs=agent_logs or _default_agent_logs(),
        )


def _default_agent_logs() -> list[AgentLogConfig]:
    return [
        AgentLogConfig(name="digest", path=agent_alert_log("digest")),
        AgentLogConfig(name="sentinel", path=agent_alert_log("sentinel")),
        AgentLogConfig(name="watchdog", path=agent_alert_log("watchdog")),
    ]


# -- Offset tracking ---------------------------------------------------------


OFFSETS_PATH = agent_data_dir("prepper") / "watch-offsets.json"


def load_offsets(path: Path | None = None) -> dict[str, int]:
    p = path or OFFSETS_PATH
    if p.exists():
        return json.loads(p.read_text())
    return {}


def save_offsets(offsets: dict[str, int], path: Path | None = None) -> None:
    p = path or OFFSETS_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(offsets))


# -- Watch loop --------------------------------------------------------------


def watch_once(
    config: PrepperWatchConfig,
    *,
    offsets_path: Path | None = None,
) -> list[dict]:
    """Poll all agent logs for new entries since last check.

    Returns a list of parsed alert dicts, each tagged with ``_agent``.
    """
    offsets = load_offsets(offsets_path)
    all_new: list[dict] = []

    for log_cfg in config.agent_logs:
        if not log_cfg.path.exists():
            continue

        current_size = log_cfg.path.stat().st_size
        key = str(log_cfg.path)
        last_offset = offsets.get(key, 0)

        # File was truncated or rotated -- reset
        if current_size < last_offset:
            last_offset = 0

        if current_size <= last_offset:
            continue

        with log_cfg.path.open() as f:
            f.seek(last_offset)
            new_data = f.read()
            offsets[key] = f.tell()

        for line in new_data.strip().splitlines():
            try:
                data = json.loads(line)
                data["_agent"] = log_cfg.name
                all_new.append(data)
            except (json.JSONDecodeError, ValueError):
                continue

    save_offsets(offsets, offsets_path)

    # Persist to unified log
    if all_new:
        unified = config.notifications.log_file
        unified.parent.mkdir(parents=True, exist_ok=True)
        with unified.open("a") as f:
            for entry in all_new:
                f.write(json.dumps(entry) + "\n")

    # Fire macOS notifications
    if config.notifications.macos and all_new:
        for entry in all_new:
            agent = entry.get("_agent", "unknown")
            severity = (entry.get("severity", "info")).upper()
            message = entry.get("message", "")
            rule = entry.get("rule_name") or entry.get("rule") or entry.get("check_name", "")
            notify_macos(
                title=f"{agent.capitalize()}: {rule}",
                body=f"[{severity}] {message}",
                group=f"prepper-{agent}",
                use_osascript=config.notifications.osascript,
            )

    return all_new


def watch_loop(
    config: PrepperWatchConfig,
    *,
    console_print: object | None = None,
) -> None:
    """Infinite poll loop. Ctrl+C to stop."""
    interval = config.poll_interval_minutes * 60
    while True:
        new = watch_once(config)
        if console_print and callable(console_print):
            console_print(f"Polled {len(config.agent_logs)} agent log(s): {len(new)} new alert(s)")
        time.sleep(interval)


# -- Unified log reader ------------------------------------------------------


def read_unified_log(
    log_path: Path | None = None,
    limit: int = 20,
    agent_filter: str | None = None,
) -> list[dict]:
    """Read the unified alert log, newest first.

    Falls back to reading individual agent logs if the unified log is empty.
    """
    path = log_path or agent_alert_log("prepper")
    entries: list[dict] = []

    if path.exists():
        lines = path.read_text().strip().splitlines()
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if agent_filter and data.get("_agent") != agent_filter:
                    continue
                entries.append(data)
                if len(entries) >= limit:
                    break
            except (json.JSONDecodeError, ValueError):
                continue
        if entries:
            return entries

    # Fallback: read individual agent logs directly
    for log_cfg in _default_agent_logs():
        if agent_filter and log_cfg.name != agent_filter:
            continue
        if not log_cfg.path.exists():
            continue
        lines = log_cfg.path.read_text().strip().splitlines()
        for line in reversed(lines):
            try:
                data = json.loads(line)
                data["_agent"] = log_cfg.name
                entries.append(data)
            except (json.JSONDecodeError, ValueError):
                continue

    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]
