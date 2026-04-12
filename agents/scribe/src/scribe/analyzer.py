"""Session-level analysis: tool usage, files touched, corrections, preferences."""

from __future__ import annotations

import re
from datetime import datetime

from scribe.models import SessionAnalysis, SessionMessage, ToolCall

# Patterns that indicate user is correcting Claude
_CORRECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^no[,.]?\s", re.IGNORECASE),
    re.compile(r"\bthat'?s\s+(not\s+)?(wrong|incorrect)\b", re.IGNORECASE),
    re.compile(r"\bnot\s+what\s+I\s+(meant|asked|wanted)\b", re.IGNORECASE),
    re.compile(r"\bactually[,.]?\s", re.IGNORECASE),
    re.compile(r"\bI\s+said\b", re.IGNORECASE),
    re.compile(r"\btry\s+again\b", re.IGNORECASE),
    re.compile(r"\bundo\s+that\b", re.IGNORECASE),
    re.compile(r"\brevert\s+(that|this|it)\b", re.IGNORECASE),
    re.compile(r"\bstop\b", re.IGNORECASE),
    re.compile(r"\bwait\b", re.IGNORECASE),
    re.compile(r"\bnot\s+\w+[,]\s*\w+\b", re.IGNORECASE),  # "not X, Y" pattern
]

# Patterns that indicate user expressing a preference
_PREFERENCE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bI\s+prefer\b", re.IGNORECASE),
    re.compile(r"\balways\s+use\b", re.IGNORECASE),
    re.compile(r"\bnever\s+use\b", re.IGNORECASE),
    re.compile(r"\bfrom\s+now\s+on\b", re.IGNORECASE),
    re.compile(r"\bmy\s+(convention|preference|style)\s+is\b", re.IGNORECASE),
    re.compile(r"\bI\s+(like|want)\s+\w+\s+over\b", re.IGNORECASE),
    re.compile(r"\bI\s+always\b", re.IGNORECASE),
    re.compile(r"\bdon'?t\s+ever\b", re.IGNORECASE),
]

# Common error indicators in command output
_ERROR_INDICATORS: list[str] = [
    "error:",
    "Error:",
    "ERROR:",
    "FAILED",
    "Failed",
    "Traceback (most recent call last)",
    "command not found",
    "No such file or directory",
    "Permission denied",
    "exit code 1",
    "Exit code 1",
    "ModuleNotFoundError",
    "ImportError",
    "SyntaxError",
    "NameError",
    "TypeError",
    "ValueError",
    "KeyError",
    "AttributeError",
    "FileNotFoundError",
    "panic:",
    "PANIC",
    "** (Mix)",
    "** (CompileError)",
]


def analyze_session(
    messages: list[SessionMessage],
    session_id: str,
    project_path: str | None = None,
) -> SessionAnalysis:
    """Produce a SessionAnalysis from parsed session messages."""
    analysis = SessionAnalysis(
        session_id=session_id,
        project=_project_name(project_path) if project_path else None,
        project_path=project_path,
    )

    analysis.message_count = len(messages)
    analysis.duration_seconds = _compute_duration(messages)

    all_tool_calls: list[ToolCall] = []

    for msg in messages:
        if msg.type == "user":
            analysis.user_message_count += 1
            analysis.user_texts.append(msg.content)
        elif msg.type == "assistant":
            analysis.assistant_message_count += 1
            all_tool_calls.extend(msg.tool_calls)

    # Tool usage profile
    for tc in all_tool_calls:
        analysis.tool_usage[tc.name] = analysis.tool_usage.get(tc.name, 0) + 1

    # Files touched
    read, edited, created = _extract_files_touched(all_tool_calls)
    analysis.files_read = read
    analysis.files_edited = edited
    analysis.files_created = created

    # Commands
    all_cmds, failed = _extract_commands(all_tool_calls)
    analysis.commands_run = all_cmds
    analysis.failed_commands = failed

    # Corrections and preferences
    analysis.corrections = _detect_corrections(messages)
    analysis.preferences = _detect_preferences(messages)

    return analysis


def _project_name(project_path: str) -> str:
    """Extract project name from path."""
    parts = project_path.rstrip("/").rsplit("/", 1)
    return parts[-1] if parts else project_path


def _compute_duration(messages: list[SessionMessage]) -> float | None:
    """Duration from first to last message timestamp, in seconds."""
    timestamps: list[datetime] = []
    for msg in messages:
        if msg.timestamp:
            try:
                if isinstance(msg.timestamp, str):
                    ts = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
                else:
                    ts = datetime.fromtimestamp(float(msg.timestamp) / 1000)
                timestamps.append(ts)
            except (ValueError, TypeError, OSError):
                continue

    if len(timestamps) < 2:
        return None

    timestamps.sort()
    delta = timestamps[-1] - timestamps[0]
    return delta.total_seconds()


def _detect_corrections(messages: list[SessionMessage]) -> list[str]:
    """Find user messages that follow assistant messages and indicate correction."""
    corrections: list[str] = []
    prev_type: str | None = None

    for msg in messages:
        if msg.type == "user" and prev_type == "assistant":
            text = msg.content.strip()
            if text and any(p.search(text) for p in _CORRECTION_PATTERNS):
                corrections.append(text)

        if msg.type in ("user", "assistant"):
            prev_type = msg.type

    return corrections


def _detect_preferences(messages: list[SessionMessage]) -> list[str]:
    """Find user messages expressing preferences."""
    preferences: list[str] = []

    for msg in messages:
        if msg.type != "user":
            continue
        text = msg.content.strip()
        if text and any(p.search(text) for p in _PREFERENCE_PATTERNS):
            preferences.append(text)

    return preferences


def _extract_files_touched(
    tool_calls: list[ToolCall],
) -> tuple[list[str], list[str], list[str]]:
    """Extract (read, edited, created) file lists from tool calls."""
    read: list[str] = []
    edited: list[str] = []
    created: list[str] = []

    seen_files: set[str] = set()

    for tc in tool_calls:
        fp = tc.input.get("file_path", "")
        if not fp:
            continue

        if tc.name == "Read" and fp not in seen_files:
            read.append(fp)
        elif tc.name == "Edit" and fp not in seen_files:
            edited.append(fp)
            seen_files.add(fp)
        elif tc.name == "Write":
            # Write to a file we already read = edit; new file = create
            if fp in {f for f in read}:
                edited.append(fp)
            else:
                created.append(fp)
            seen_files.add(fp)

    return read, edited, created


def _extract_commands(
    tool_calls: list[ToolCall],
) -> tuple[list[str], list[str]]:
    """Extract (all_commands, failed_commands) from Bash tool calls.

    A command is considered failed if its input contains ``description``
    hints with error-like wording, but since we don't have tool results
    in the session parser, we track commands that are commonly
    error-prone.  In practice, the watcher can enrich this later.
    """
    all_cmds: list[str] = []
    failed: list[str] = []

    for tc in tool_calls:
        if tc.name != "Bash":
            continue

        cmd = tc.input.get("command", "")
        if not cmd:
            continue

        all_cmds.append(cmd)

    return all_cmds, failed
