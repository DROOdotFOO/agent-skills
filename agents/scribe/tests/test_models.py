"""Tests for scribe data models."""

from recall.models import EntryType

from scribe.models import (
    INSIGHT_TO_ENTRY_TYPE,
    InsightType,
    ScribeActivity,
    SessionAnalysis,
    SessionMessage,
    ToolCall,
    WatchState,
)


def test_insight_type_to_entry_type_mapping_complete():
    """Every InsightType maps to an EntryType."""
    for it in InsightType:
        assert it in INSIGHT_TO_ENTRY_TYPE


def test_correction_maps_to_gotcha():
    assert INSIGHT_TO_ENTRY_TYPE[InsightType.CORRECTION] == EntryType.GOTCHA


def test_preference_maps_to_decision():
    assert INSIGHT_TO_ENTRY_TYPE[InsightType.PREFERENCE] == EntryType.DECISION


def test_repeated_failure_maps_to_gotcha():
    assert INSIGHT_TO_ENTRY_TYPE[InsightType.REPEATED_FAILURE] == EntryType.GOTCHA


def test_tool_call_defaults():
    tc = ToolCall(name="Read")
    assert tc.input == {}
    assert tc.timestamp is None


def test_session_message_defaults():
    msg = SessionMessage(type="user", content="hello")
    assert msg.tool_calls == []
    assert msg.timestamp is None
    assert msg.uuid is None


def test_session_analysis_defaults():
    sa = SessionAnalysis(session_id="test-001")
    assert sa.project is None
    assert sa.tool_usage == {}
    assert sa.files_read == []
    assert sa.corrections == []
    assert sa.user_texts == []


def test_scribe_activity_has_timestamp():
    act = ScribeActivity(session_id="sess-001")
    assert act.timestamp  # auto-generated
    assert act.insights_generated == 0


def test_watch_state_defaults():
    ws = WatchState()
    assert ws.sessions_tracked == {}
    assert ws.sessions_analyzed == []
    assert ws.last_poll_ts == 0.0


def test_watch_state_roundtrip():
    ws = WatchState(
        sessions_tracked={"sess-001": 1776000000.0},
        sessions_analyzed=["sess-000"],
        session_projects={"sess-001": "/Users/test/proj"},
        last_poll_ts=1776000000.0,
    )
    data = ws.model_dump()
    ws2 = WatchState.model_validate(data)
    assert ws2.sessions_tracked == ws.sessions_tracked
    assert ws2.sessions_analyzed == ws.sessions_analyzed
    assert ws2.last_poll_ts == ws.last_poll_ts
