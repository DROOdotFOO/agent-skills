"""Parse Claude Code session JSONL files into structured messages."""

from __future__ import annotations

import json
from pathlib import Path

from scribe.models import SessionMessage, ToolCall

CLAUDE_DIR = Path.home() / ".claude"


def project_path_to_key(project_path: str) -> str:
    """Convert a project path to the Claude Code project directory key.

    ``/Users/droo/CODE/agent-skills`` -> ``-Users-droo-CODE-agent-skills``
    """
    return project_path.replace("/", "-")


def session_jsonl_path(
    session_id: str,
    project_path: str,
    *,
    claude_dir: Path | None = None,
) -> Path:
    """Return the full path to a session's JSONL file."""
    base = claude_dir or CLAUDE_DIR
    key = project_path_to_key(project_path)
    return base / "projects" / key / f"{session_id}.jsonl"


def parse_session(
    session_id: str,
    project_path: str,
    *,
    claude_dir: Path | None = None,
) -> list[SessionMessage]:
    """Parse a session JSONL into structured messages.

    Reads ``~/.claude/projects/{key}/{sessionId}.jsonl`` and extracts user
    messages, assistant messages (with tool_use blocks), and system messages.
    Skips malformed lines and non-message types gracefully.
    """
    path = session_jsonl_path(session_id, project_path, claude_dir=claude_dir)
    if not path.exists():
        return []

    messages: list[SessionMessage] = []

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = record.get("type", "")
            if msg_type not in ("user", "assistant", "system"):
                continue

            # Skip meta messages (local command caveats, etc.)
            if record.get("isMeta"):
                continue

            timestamp = record.get("timestamp")
            uuid = record.get("uuid")

            if msg_type == "system":
                content = record.get("content", "")
                messages.append(
                    SessionMessage(
                        type=msg_type,
                        content=content if isinstance(content, str) else "",
                        timestamp=timestamp,
                        uuid=uuid,
                    )
                )
                continue

            message = record.get("message", {})
            if not isinstance(message, dict):
                continue

            raw_content = message.get("content", "")
            text = _extract_text_content(raw_content)
            tool_calls = _extract_tool_calls(raw_content, timestamp)

            messages.append(
                SessionMessage(
                    type=msg_type,
                    content=text,
                    tool_calls=tool_calls,
                    timestamp=timestamp,
                    uuid=uuid,
                )
            )

    return messages


def _extract_text_content(content: str | list) -> str:
    """Extract text from message content (handles str and list-of-dicts)."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "thinking":
                    # Skip thinking blocks -- internal reasoning
                    pass
        return "\n".join(parts)

    return ""


def _extract_tool_calls(content: str | list, timestamp: str | None = None) -> list[ToolCall]:
    """Extract tool_use blocks from assistant message content."""
    if not isinstance(content, list):
        return []

    calls: list[ToolCall] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            calls.append(
                ToolCall(
                    name=block.get("name", "unknown"),
                    input=block.get("input", {}),
                    timestamp=timestamp,
                )
            )

    return calls
