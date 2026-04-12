"""Tests for session JSONL parsing."""

from __future__ import annotations

import json
from pathlib import Path

from scribe.session_parser import (
    parse_session,
    project_path_to_key,
    session_jsonl_path,
)


def test_project_path_to_key_basic():
    assert project_path_to_key("/Users/droo/CODE/foo") == "-Users-droo-CODE-foo"


def test_project_path_to_key_nested():
    assert project_path_to_key("/Users/droo/CODE/agent-skills") == "-Users-droo-CODE-agent-skills"


def test_session_jsonl_path(tmp_claude_dir: Path):
    path = session_jsonl_path("sess-001", "/Users/test/proj-a", claude_dir=tmp_claude_dir)
    assert path == tmp_claude_dir / "projects" / "-Users-test-proj-a" / "sess-001.jsonl"


def test_parse_session_returns_messages(sample_session: tuple[str, str, Path]):
    session_id, project_path, claude_dir = sample_session
    messages = parse_session(session_id, project_path, claude_dir=claude_dir)

    # 3 user + 3 assistant + 1 system = 7
    assert len(messages) == 7

    user_msgs = [m for m in messages if m.type == "user"]
    assert len(user_msgs) == 3

    assistant_msgs = [m for m in messages if m.type == "assistant"]
    assert len(assistant_msgs) == 3

    system_msgs = [m for m in messages if m.type == "system"]
    assert len(system_msgs) == 1


def test_parse_session_extracts_tool_calls(sample_session: tuple[str, str, Path]):
    session_id, project_path, claude_dir = sample_session
    messages = parse_session(session_id, project_path, claude_dir=claude_dir)

    assistant_msgs = [m for m in messages if m.type == "assistant"]

    # First assistant has Read + Bash
    first = assistant_msgs[0]
    assert len(first.tool_calls) == 2
    assert first.tool_calls[0].name == "Read"
    assert first.tool_calls[0].input["file_path"] == "/Users/test/proj-a/store.py"
    assert first.tool_calls[1].name == "Bash"

    # Second assistant has Edit
    second = assistant_msgs[1]
    assert len(second.tool_calls) == 1
    assert second.tool_calls[0].name == "Edit"

    # Third assistant has Write
    third = assistant_msgs[2]
    assert len(third.tool_calls) == 1
    assert third.tool_calls[0].name == "Write"


def test_parse_session_extracts_user_text(sample_session: tuple[str, str, Path]):
    session_id, project_path, claude_dir = sample_session
    messages = parse_session(session_id, project_path, claude_dir=claude_dir)

    user_msgs = [m for m in messages if m.type == "user"]
    assert "SQLite" in user_msgs[0].content
    assert "sqlite3" in user_msgs[1].content
    assert "pathlib" in user_msgs[2].content


def test_parse_session_nonexistent_returns_empty(tmp_claude_dir: Path):
    messages = parse_session("nonexistent", "/fake/path", claude_dir=tmp_claude_dir)
    assert messages == []


def test_parse_session_skips_malformed_lines(tmp_claude_dir: Path):
    project_path = "/Users/test/proj"
    key = project_path.replace("/", "-")
    project_dir = tmp_claude_dir / "projects" / key
    project_dir.mkdir(parents=True)
    session_file = project_dir / "sess-bad.jsonl"

    with session_file.open("w") as f:
        f.write("not valid json\n")
        f.write(
            json.dumps(
                {
                    "type": "user",
                    "message": {"role": "user", "content": "valid message"},
                    "timestamp": "2026-04-12T10:00:00.000Z",
                    "uuid": "uuid-001",
                }
            )
            + "\n"
        )
        f.write("\n")  # blank line

    messages = parse_session("sess-bad", project_path, claude_dir=tmp_claude_dir)
    assert len(messages) == 1
    assert messages[0].content == "valid message"


def test_parse_session_skips_meta_messages(tmp_claude_dir: Path):
    project_path = "/Users/test/proj"
    key = project_path.replace("/", "-")
    project_dir = tmp_claude_dir / "projects" / key
    project_dir.mkdir(parents=True)
    session_file = project_dir / "sess-meta.jsonl"

    with session_file.open("w") as f:
        f.write(
            json.dumps(
                {
                    "type": "user",
                    "message": {"role": "user", "content": "meta caveat"},
                    "isMeta": True,
                    "timestamp": "2026-04-12T10:00:00.000Z",
                    "uuid": "uuid-meta",
                }
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {
                    "type": "user",
                    "message": {"role": "user", "content": "real message"},
                    "timestamp": "2026-04-12T10:00:01.000Z",
                    "uuid": "uuid-real",
                }
            )
            + "\n"
        )

    messages = parse_session("sess-meta", project_path, claude_dir=tmp_claude_dir)
    assert len(messages) == 1
    assert messages[0].content == "real message"


def test_parse_session_skips_non_message_types(tmp_claude_dir: Path):
    project_path = "/Users/test/proj"
    key = project_path.replace("/", "-")
    project_dir = tmp_claude_dir / "projects" / key
    project_dir.mkdir(parents=True)
    session_file = project_dir / "sess-types.jsonl"

    with session_file.open("w") as f:
        f.write(
            json.dumps(
                {
                    "type": "file-history-snapshot",
                    "messageId": "mid-001",
                    "snapshot": {},
                }
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {
                    "type": "queue-operation",
                    "operation": "clear",
                }
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {
                    "type": "last-prompt",
                    "lastPrompt": "test",
                }
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {
                    "type": "user",
                    "message": {"role": "user", "content": "actual message"},
                    "timestamp": "2026-04-12T10:00:00.000Z",
                    "uuid": "uuid-001",
                }
            )
            + "\n"
        )

    messages = parse_session("sess-types", project_path, claude_dir=tmp_claude_dir)
    assert len(messages) == 1
    assert messages[0].type == "user"


def test_parse_session_handles_string_content_in_user_msg(tmp_claude_dir: Path):
    """User messages can have content as a plain string."""
    project_path = "/Users/test/proj"
    key = project_path.replace("/", "-")
    project_dir = tmp_claude_dir / "projects" / key
    project_dir.mkdir(parents=True)
    session_file = project_dir / "sess-str.jsonl"

    with session_file.open("w") as f:
        f.write(
            json.dumps(
                {
                    "type": "user",
                    "message": {"role": "user", "content": "plain string content"},
                    "timestamp": "2026-04-12T10:00:00.000Z",
                    "uuid": "uuid-001",
                }
            )
            + "\n"
        )

    messages = parse_session("sess-str", project_path, claude_dir=tmp_claude_dir)
    assert len(messages) == 1
    assert messages[0].content == "plain string content"


def test_parse_session_system_message_content(tmp_claude_dir: Path):
    project_path = "/Users/test/proj"
    key = project_path.replace("/", "-")
    project_dir = tmp_claude_dir / "projects" / key
    project_dir.mkdir(parents=True)
    session_file = project_dir / "sess-sys.jsonl"

    with session_file.open("w") as f:
        f.write(
            json.dumps(
                {
                    "type": "system",
                    "content": "Context loaded",
                    "subtype": "info",
                    "level": "info",
                    "timestamp": "2026-04-12T10:00:00.000Z",
                    "uuid": "uuid-sys",
                }
            )
            + "\n"
        )

    messages = parse_session("sess-sys", project_path, claude_dir=tmp_claude_dir)
    assert len(messages) == 1
    assert messages[0].type == "system"
    assert messages[0].content == "Context loaded"
