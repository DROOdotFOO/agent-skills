"""Notification dispatch for digest alerts.

Supports macOS native notifications (osascript + terminal-notifier) and
JSONL alert log persistence.
"""

from __future__ import annotations

import contextlib
import shutil
import subprocess
from pathlib import Path

from shared.paths import agent_alert_log

from digest.alerts import DigestAlert

DEFAULT_LOG_PATH = agent_alert_log("digest")


def append_to_log(alerts: list[DigestAlert], log_path: Path | None = None) -> None:
    """Append alerts to a JSONL log file."""
    path = log_path or DEFAULT_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        for alert in alerts:
            f.write(alert.model_dump_json() + "\n")


def read_log(log_path: Path | None = None, limit: int = 20) -> list[DigestAlert]:
    """Read recent alerts from the JSONL log, newest first."""
    path = log_path or DEFAULT_LOG_PATH
    if not path.exists():
        return []
    lines = path.read_text().strip().splitlines()
    recent = lines[-limit:] if limit else lines
    alerts: list[DigestAlert] = []
    for line in reversed(recent):
        try:
            alerts.append(DigestAlert.model_validate_json(line))
        except Exception:
            continue
    return alerts


def notify_macos(alerts: list[DigestAlert], *, use_osascript: bool = True) -> None:
    """Send macOS notifications for alerts.

    Tries terminal-notifier first (richer UI, clickable), falls back to
    osascript (always available on macOS).
    """
    if not alerts:
        return

    has_terminal_notifier = shutil.which("terminal-notifier") is not None

    for alert in alerts:
        title = f"Digest: {alert.topic}"
        body = f"[{alert.severity.value.upper()}] {alert.message}"

        if has_terminal_notifier:
            _notify_terminal_notifier(title, body, alert)

        if use_osascript:
            _notify_osascript(title, body)


def _notify_terminal_notifier(title: str, body: str, alert: DigestAlert) -> None:
    """Send notification via terminal-notifier (brew install terminal-notifier)."""
    cmd = [
        "terminal-notifier",
        "-title",
        title,
        "-message",
        body,
        "-group",
        f"digest-{alert.topic}",
    ]
    if alert.items:
        cmd.extend(["-open", alert.items[0]])
    with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
        subprocess.run(cmd, capture_output=True, timeout=5)


def _notify_osascript(title: str, body: str) -> None:
    """Send notification via osascript (always available on macOS)."""
    escaped_body = _escape_applescript(body)
    escaped_title = _escape_applescript(title)
    script = f'display notification "{escaped_body}" with title "{escaped_title}"'
    with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
        )


def _escape_applescript(text: str) -> str:
    """Escape special characters for AppleScript strings."""
    return text.replace("\\", "\\\\").replace('"', '\\"')
