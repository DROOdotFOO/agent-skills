"""Shared fixtures for scribe tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_claude_dir(tmp_path: Path) -> Path:
    """Create a Claude-like directory structure for testing."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "projects").mkdir()
    return claude_dir


@pytest.fixture()
def sample_history(tmp_claude_dir: Path) -> Path:
    """Write a synthetic history.jsonl with multiple sessions."""
    history = tmp_claude_dir / "history.jsonl"
    entries = [
        {
            "display": "let's go with SQLite for the storage backend",
            "timestamp": 1776000000000,
            "project": "/Users/test/proj-a",
            "sessionId": "sess-001",
        },
        {
            "display": "no, I meant use the built-in sqlite3 module",
            "timestamp": 1776000060000,
            "project": "/Users/test/proj-a",
            "sessionId": "sess-001",
        },
        {
            "display": "I prefer pathlib over os.path",
            "timestamp": 1776000120000,
            "project": "/Users/test/proj-a",
            "sessionId": "sess-001",
        },
        {
            "display": "run the tests",
            "timestamp": 1776003600000,
            "project": "/Users/test/proj-b",
            "sessionId": "sess-002",
        },
    ]
    with history.open("w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return history


def _make_user_msg(
    content: str,
    session_id: str = "sess-001",
    cwd: str = "/Users/test/proj-a",
    timestamp: str = "2026-04-12T10:00:00.000Z",
) -> dict:
    return {
        "parentUuid": None,
        "isSidechain": False,
        "type": "user",
        "message": {"role": "user", "content": content},
        "uuid": f"uuid-{hash(content) % 10000:04d}",
        "timestamp": timestamp,
        "userType": "external",
        "entrypoint": "cli",
        "cwd": cwd,
        "sessionId": session_id,
        "version": "2.1.91",
        "gitBranch": "main",
    }


def _make_assistant_msg(
    text: str = "",
    tool_calls: list[dict] | None = None,
    timestamp: str = "2026-04-12T10:00:05.000Z",
) -> dict:
    content: list[dict] = []
    if text:
        content.append({"type": "text", "text": text})
    for tc in tool_calls or []:
        content.append(
            {
                "type": "tool_use",
                "id": f"toolu_{hash(str(tc)) % 100000:05d}",
                "name": tc["name"],
                "input": tc.get("input", {}),
            }
        )
    return {
        "parentUuid": None,
        "isSidechain": False,
        "type": "assistant",
        "message": {"role": "assistant", "content": content},
        "uuid": f"uuid-asst-{hash(text) % 10000:04d}",
        "timestamp": timestamp,
    }


def _make_system_msg(content: str = "", timestamp: str = "2026-04-12T10:00:00.000Z") -> dict:
    return {
        "parentUuid": None,
        "isSidechain": False,
        "type": "system",
        "subtype": "info",
        "content": content,
        "level": "info",
        "timestamp": timestamp,
        "uuid": f"uuid-sys-{hash(content) % 10000:04d}",
    }


@pytest.fixture()
def sample_session(tmp_claude_dir: Path) -> tuple[str, str, Path]:
    """Write a synthetic session JSONL and return (session_id, project_path, claude_dir)."""
    session_id = "sess-001"
    project_path = "/Users/test/proj-a"
    project_key = project_path.replace("/", "-")
    project_dir = tmp_claude_dir / "projects" / project_key
    project_dir.mkdir(parents=True)

    session_file = project_dir / f"{session_id}.jsonl"
    messages = [
        _make_user_msg(
            "let's go with SQLite for the storage backend",
            timestamp="2026-04-12T10:00:00.000Z",
        ),
        _make_assistant_msg(
            text="I'll set up SQLite.",
            tool_calls=[
                {"name": "Read", "input": {"file_path": "/Users/test/proj-a/store.py"}},
                {"name": "Bash", "input": {"command": "python -m pytest tests/ -v"}},
            ],
            timestamp="2026-04-12T10:00:05.000Z",
        ),
        _make_user_msg(
            "no, I meant use the built-in sqlite3 module not sqlalchemy",
            timestamp="2026-04-12T10:00:30.000Z",
        ),
        _make_assistant_msg(
            text="Got it, switching to sqlite3.",
            tool_calls=[
                {
                    "name": "Edit",
                    "input": {
                        "file_path": "/Users/test/proj-a/store.py",
                        "old_string": "import sqlalchemy",
                        "new_string": "import sqlite3",
                    },
                },
            ],
            timestamp="2026-04-12T10:00:35.000Z",
        ),
        _make_user_msg(
            "I prefer pathlib over os.path always",
            timestamp="2026-04-12T10:01:00.000Z",
        ),
        _make_assistant_msg(
            text="Noted, using pathlib.",
            tool_calls=[
                {
                    "name": "Write",
                    "input": {
                        "file_path": "/Users/test/proj-a/utils.py",
                        "content": "from pathlib import Path\n",
                    },
                },
            ],
            timestamp="2026-04-12T10:01:05.000Z",
        ),
        _make_system_msg("Session context loaded", timestamp="2026-04-12T10:00:00.000Z"),
    ]

    with session_file.open("w") as f:
        for msg in messages:
            f.write(json.dumps(msg) + "\n")

    return session_id, project_path, tmp_claude_dir
