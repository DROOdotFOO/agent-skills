"""Agent-agnostic notification dispatch and JSONL log persistence.

Extracted from digest's notifier.py and made generic so any agent can
append Pydantic models to a JSONL log and send macOS notifications.
"""

from __future__ import annotations

import contextlib
import shutil
import subprocess
from pathlib import Path

from pydantic import BaseModel


def append_to_log(items: list[BaseModel], log_path: Path) -> None:
    """Append Pydantic models as JSONL lines to *log_path*."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        for item in items:
            f.write(item.model_dump_json() + "\n")


def read_log_lines(log_path: Path, limit: int = 20) -> list[str]:
    """Read recent JSONL lines from *log_path*, newest first.

    Returns raw JSON strings so callers can deserialize to their own models.
    """
    if not log_path.exists():
        return []
    lines = log_path.read_text().strip().splitlines()
    recent = lines[-limit:] if limit else lines
    return list(reversed(recent))


def notify_macos(
    title: str,
    body: str,
    *,
    group: str = "",
    open_url: str = "",
    use_osascript: bool = True,
) -> None:
    """Send a macOS notification via terminal-notifier and/or osascript.

    Args:
        title: Notification title.
        body: Notification body text.
        group: Grouping key for terminal-notifier (collapses duplicates).
        open_url: URL to open when notification is clicked.
        use_osascript: Also send via osascript (always available on macOS).
    """
    has_terminal_notifier = shutil.which("terminal-notifier") is not None

    if has_terminal_notifier:
        cmd = ["terminal-notifier", "-title", title, "-message", body]
        if group:
            cmd.extend(["-group", group])
        if open_url:
            cmd.extend(["-open", open_url])
        with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
            subprocess.run(cmd, capture_output=True, timeout=5)

    if use_osascript:
        escaped_body = _escape_applescript(body)
        escaped_title = _escape_applescript(title)
        script = f'display notification "{escaped_body}" with title "{escaped_title}"'
        with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)


def _escape_applescript(text: str) -> str:
    """Escape special characters for AppleScript strings."""
    return text.replace("\\", "\\\\").replace('"', '\\"')
