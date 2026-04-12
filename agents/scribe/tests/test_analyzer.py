"""Tests for session analysis."""

from scribe.analyzer import (
    _compute_duration,
    _detect_corrections,
    _detect_preferences,
    _extract_commands,
    _extract_files_touched,
    analyze_session,
)
from scribe.models import SessionMessage, ToolCall


def _user(content: str, ts: str = "2026-04-12T10:00:00.000Z") -> SessionMessage:
    return SessionMessage(type="user", content=content, timestamp=ts)


def _asst(
    text: str = "",
    tool_calls: list[ToolCall] | None = None,
    ts: str = "2026-04-12T10:00:05.000Z",
) -> SessionMessage:
    return SessionMessage(
        type="assistant",
        content=text,
        tool_calls=tool_calls or [],
        timestamp=ts,
    )


# -- analyze_session ----------------------------------------------------------


def test_analyze_session_counts(sample_session):
    from scribe.session_parser import parse_session

    sid, project_path, claude_dir = sample_session
    messages = parse_session(sid, project_path, claude_dir=claude_dir)
    analysis = analyze_session(messages, sid, project_path)

    assert analysis.session_id == sid
    assert analysis.project == "proj-a"
    assert analysis.user_message_count == 3
    assert analysis.assistant_message_count == 3
    assert analysis.message_count == 7  # 3+3+1 system


def test_analyze_session_tool_usage(sample_session):
    from scribe.session_parser import parse_session

    sid, project_path, claude_dir = sample_session
    messages = parse_session(sid, project_path, claude_dir=claude_dir)
    analysis = analyze_session(messages, sid, project_path)

    assert analysis.tool_usage["Read"] == 1
    assert analysis.tool_usage["Bash"] == 1
    assert analysis.tool_usage["Edit"] == 1
    assert analysis.tool_usage["Write"] == 1


def test_analyze_session_files(sample_session):
    from scribe.session_parser import parse_session

    sid, project_path, claude_dir = sample_session
    messages = parse_session(sid, project_path, claude_dir=claude_dir)
    analysis = analyze_session(messages, sid, project_path)

    assert "/Users/test/proj-a/store.py" in analysis.files_read
    assert "/Users/test/proj-a/store.py" in analysis.files_edited
    assert "/Users/test/proj-a/utils.py" in analysis.files_created


def test_analyze_session_commands(sample_session):
    from scribe.session_parser import parse_session

    sid, project_path, claude_dir = sample_session
    messages = parse_session(sid, project_path, claude_dir=claude_dir)
    analysis = analyze_session(messages, sid, project_path)

    assert "python -m pytest tests/ -v" in analysis.commands_run


# -- corrections --------------------------------------------------------------


def test_detect_corrections_no_prefix():
    msgs = [_asst("I'll do X"), _user("no, do Y instead")]
    assert len(_detect_corrections(msgs)) == 1


def test_detect_corrections_thats_wrong():
    msgs = [_asst("done"), _user("that's wrong, the file should be in src/")]
    assert len(_detect_corrections(msgs)) == 1


def test_detect_corrections_not_what_i_meant():
    msgs = [_asst("here"), _user("not what I meant, use pathlib")]
    assert len(_detect_corrections(msgs)) == 1


def test_detect_corrections_actually():
    msgs = [_asst("set up"), _user("actually, let's use a different approach")]
    assert len(_detect_corrections(msgs)) == 1


def test_detect_corrections_try_again():
    msgs = [_asst("done"), _user("try again with the correct import")]
    assert len(_detect_corrections(msgs)) == 1


def test_detect_corrections_requires_preceding_assistant():
    msgs = [_user("no, do Y instead")]
    assert len(_detect_corrections(msgs)) == 0


def test_detect_corrections_skips_user_to_user():
    msgs = [_user("first"), _user("no, second")]
    assert len(_detect_corrections(msgs)) == 0


def test_detect_corrections_stop():
    msgs = [_asst("writing"), _user("stop, that's not right")]
    assert len(_detect_corrections(msgs)) == 1


def test_detect_corrections_wait():
    msgs = [_asst("proceeding"), _user("wait, I need to check something")]
    assert len(_detect_corrections(msgs)) == 1


# -- preferences ---------------------------------------------------------------


def test_detect_preferences_i_prefer():
    msgs = [_user("I prefer pathlib over os.path")]
    assert len(_detect_preferences(msgs)) == 1


def test_detect_preferences_always_use():
    msgs = [_user("always use type hints")]
    assert len(_detect_preferences(msgs)) == 1


def test_detect_preferences_never_use():
    msgs = [_user("never use mocks in tests")]
    assert len(_detect_preferences(msgs)) == 1


def test_detect_preferences_from_now_on():
    msgs = [_user("from now on, use ruff instead of black")]
    assert len(_detect_preferences(msgs)) == 1


def test_detect_preferences_my_convention():
    msgs = [_user("my convention is snake_case for variables")]
    assert len(_detect_preferences(msgs)) == 1


def test_detect_preferences_dont_ever():
    msgs = [_user("don't ever commit directly to main")]
    assert len(_detect_preferences(msgs)) == 1


def test_detect_preferences_skips_assistant():
    msgs = [_asst("I prefer to use pathlib")]
    assert len(_detect_preferences(msgs)) == 0


def test_detect_preferences_no_match():
    msgs = [_user("run the tests")]
    assert len(_detect_preferences(msgs)) == 0


# -- files touched -------------------------------------------------------------


def test_extract_files_read():
    calls = [ToolCall(name="Read", input={"file_path": "/a/b.py"})]
    read, edited, created = _extract_files_touched(calls)
    assert "/a/b.py" in read
    assert edited == []
    assert created == []


def test_extract_files_edited():
    calls = [
        ToolCall(
            name="Edit",
            input={"file_path": "/a/b.py", "old_string": "x", "new_string": "y"},
        )
    ]
    read, edited, created = _extract_files_touched(calls)
    assert "/a/b.py" in edited


def test_extract_files_created():
    calls = [ToolCall(name="Write", input={"file_path": "/a/new.py", "content": "hello"})]
    read, edited, created = _extract_files_touched(calls)
    assert "/a/new.py" in created


def test_extract_files_write_after_read_is_edit():
    calls = [
        ToolCall(name="Read", input={"file_path": "/a/b.py"}),
        ToolCall(name="Write", input={"file_path": "/a/b.py", "content": "updated"}),
    ]
    read, edited, created = _extract_files_touched(calls)
    assert "/a/b.py" in read
    assert "/a/b.py" in edited
    assert "/a/b.py" not in created


# -- commands ------------------------------------------------------------------


def test_extract_commands():
    calls = [
        ToolCall(name="Bash", input={"command": "pytest -v"}),
        ToolCall(name="Bash", input={"command": "git status"}),
        ToolCall(name="Read", input={"file_path": "/a/b.py"}),
    ]
    all_cmds, failed = _extract_commands(calls)
    assert len(all_cmds) == 2
    assert "pytest -v" in all_cmds
    assert "git status" in all_cmds


def test_extract_commands_skips_empty():
    calls = [ToolCall(name="Bash", input={"command": ""})]
    all_cmds, _ = _extract_commands(calls)
    assert len(all_cmds) == 0


# -- duration ------------------------------------------------------------------


def test_compute_duration():
    msgs = [
        SessionMessage(type="user", content="a", timestamp="2026-04-12T10:00:00.000Z"),
        SessionMessage(type="assistant", content="b", timestamp="2026-04-12T10:01:00.000Z"),
    ]
    dur = _compute_duration(msgs)
    assert dur == 60.0


def test_compute_duration_single_message():
    msgs = [SessionMessage(type="user", content="a", timestamp="2026-04-12T10:00:00.000Z")]
    assert _compute_duration(msgs) is None


def test_compute_duration_no_timestamps():
    msgs = [SessionMessage(type="user", content="a")]
    assert _compute_duration(msgs) is None
