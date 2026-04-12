"""Tests for insight extraction and classification."""

from recall.models import EntryType

from scribe.extractor import _tool_pattern_insights, classify_insight_type, extract_insights
from scribe.models import InsightType, SessionAnalysis

# -- classify_insight_type -----------------------------------------------------


def test_classify_correction_no():
    assert classify_insight_type("no, use sqlite3 not sqlalchemy") == InsightType.CORRECTION


def test_classify_correction_thats_wrong():
    assert classify_insight_type("that's wrong, fix the import") == InsightType.CORRECTION


def test_classify_correction_try_again():
    assert classify_insight_type("try again with the correct path") == InsightType.CORRECTION


def test_classify_preference_i_prefer():
    assert classify_insight_type("I prefer pathlib over os.path") == InsightType.PREFERENCE


def test_classify_preference_always_use():
    assert classify_insight_type("always use type hints in Python") == InsightType.PREFERENCE


def test_classify_preference_from_now_on():
    assert classify_insight_type("from now on use ruff") == InsightType.PREFERENCE


def test_classify_decision_lets_go_with():
    assert classify_insight_type("let's go with SQLite for storage") == InsightType.DECISION


def test_classify_gotcha_avoid():
    assert classify_insight_type("avoid using mocks in integration tests") == InsightType.GOTCHA


def test_classify_default_insight():
    assert classify_insight_type("run the tests") == InsightType.INSIGHT


# -- extract_insights ----------------------------------------------------------


def test_extract_insights_from_corrections():
    analysis = SessionAnalysis(
        session_id="sess-001",
        project="proj-a",
        corrections=["no, use the built-in sqlite3 module"],
        user_texts=["something", "no, use the built-in sqlite3 module"],
    )
    entries = extract_insights(analysis)
    correction_entries = [e for e in entries if "scribe:correction" in e.tags]
    assert len(correction_entries) == 1
    assert correction_entries[0].entry_type == EntryType.GOTCHA
    assert correction_entries[0].source == "scribe:sess-001"


def test_extract_insights_from_preferences():
    analysis = SessionAnalysis(
        session_id="sess-002",
        project="proj-b",
        preferences=["I prefer pathlib over os.path always"],
        user_texts=["I prefer pathlib over os.path always"],
    )
    entries = extract_insights(analysis)
    pref_entries = [e for e in entries if "scribe:preference" in e.tags]
    assert len(pref_entries) == 1
    assert pref_entries[0].entry_type == EntryType.DECISION


def test_extract_insights_from_decision_text():
    analysis = SessionAnalysis(
        session_id="sess-003",
        project="proj-c",
        user_texts=["let's go with SQLite for the storage backend"],
    )
    entries = extract_insights(analysis)
    decision_entries = [e for e in entries if "scribe:decision" in e.tags]
    assert len(decision_entries) == 1
    assert decision_entries[0].entry_type == EntryType.DECISION


def test_extract_insights_skips_short_texts():
    analysis = SessionAnalysis(
        session_id="sess-004",
        project="proj-d",
        user_texts=["yes", "ok", "run tests"],
    )
    entries = extract_insights(analysis)
    # Short texts and generic insights should be skipped
    text_entries = [
        e
        for e in entries
        if "scribe:correction" not in e.tags
        and "scribe:preference" not in e.tags
        and "scribe:tool-pattern" not in e.tags
    ]
    assert len(text_entries) == 0


def test_extract_insights_skips_generic_insight():
    analysis = SessionAnalysis(
        session_id="sess-005",
        project="proj-e",
        user_texts=["check the file for any issues please"],
    )
    entries = extract_insights(analysis)
    # Generic text that classifies as INSIGHT (default) should be skipped
    assert len(entries) == 0


def test_extract_insights_deduplicates_correction_in_user_texts():
    """Corrections already in corrections list should not be re-extracted from user_texts."""
    text = "no, use the built-in sqlite3 module"
    analysis = SessionAnalysis(
        session_id="sess-006",
        project="proj-f",
        corrections=[text],
        user_texts=[text, "let's go with pydantic for validation"],
    )
    entries = extract_insights(analysis)
    correction_entries = [e for e in entries if "scribe:correction" in e.tags]
    # Only one correction entry, not duplicated from user_texts
    assert len(correction_entries) == 1


def test_extract_insights_tags_include_tech_terms():
    analysis = SessionAnalysis(
        session_id="sess-007",
        project="proj-g",
        corrections=["no, use sqlite3 not sqlalchemy for python"],
    )
    entries = extract_insights(analysis)
    assert len(entries) >= 1
    tags = entries[0].tags
    assert "python" in tags or "sqlite" in tags


# -- tool pattern insights -----------------------------------------------------


def test_tool_pattern_edits_without_tests():
    analysis = SessionAnalysis(
        session_id="sess-010",
        project="proj-j",
        tool_usage={"Edit": 6, "Read": 3, "Bash": 2},
        commands_run=["git status", "ls"],
    )
    entries = _tool_pattern_insights(analysis)
    assert len(entries) == 1
    assert "no test commands" in entries[0].content


def test_tool_pattern_edits_with_tests():
    analysis = SessionAnalysis(
        session_id="sess-011",
        project="proj-k",
        tool_usage={"Edit": 6, "Read": 3, "Bash": 2},
        commands_run=["pytest -v", "git status"],
    )
    entries = _tool_pattern_insights(analysis)
    assert len(entries) == 0


def test_tool_pattern_exploration_session():
    analysis = SessionAnalysis(
        session_id="sess-012",
        project="proj-l",
        tool_usage={"Read": 12, "Grep": 3},
        commands_run=[],
    )
    entries = _tool_pattern_insights(analysis)
    assert len(entries) == 1
    assert "exploration" in entries[0].content


def test_tool_pattern_below_threshold():
    analysis = SessionAnalysis(
        session_id="sess-013",
        project="proj-m",
        tool_usage={"Read": 2},
        commands_run=[],
    )
    entries = _tool_pattern_insights(analysis)
    assert len(entries) == 0
