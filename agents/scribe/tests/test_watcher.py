"""Tests for the two-phase watch loop."""

from __future__ import annotations

import json
import time
from pathlib import Path

from recall.store import Store

from scribe.models import WatchState
from scribe.watcher import (
    ScribeWatchConfig,
    discover_sessions,
    find_idle_sessions,
    load_offsets,
    load_state,
    process_session,
    save_offsets,
    save_state,
    watch_once,
)

# -- offset persistence -------------------------------------------------------


def test_load_offsets_empty(tmp_path: Path):
    offsets = load_offsets(tmp_path / "nonexistent.json")
    assert offsets == {}


def test_save_and_load_offsets(tmp_path: Path):
    path = tmp_path / "offsets.json"
    save_offsets({"file.jsonl": 1024}, path)
    loaded = load_offsets(path)
    assert loaded["file.jsonl"] == 1024


# -- state persistence --------------------------------------------------------


def test_load_state_empty(tmp_path: Path):
    state = load_state(tmp_path / "nonexistent.json")
    assert state.sessions_tracked == {}


def test_save_and_load_state(tmp_path: Path):
    path = tmp_path / "state.json"
    state = WatchState(
        sessions_tracked={"sess-001": 1776000000.0},
        sessions_analyzed=["sess-000"],
        session_projects={"sess-001": "/test/proj"},
    )
    save_state(state, path)
    loaded = load_state(path)
    assert loaded.sessions_tracked == state.sessions_tracked
    assert loaded.sessions_analyzed == state.sessions_analyzed


# -- discover_sessions ---------------------------------------------------------


def test_discover_sessions_from_history(tmp_claude_dir: Path, sample_history: Path):
    config = ScribeWatchConfig(claude_dir=tmp_claude_dir)
    state = WatchState()
    offsets_path = tmp_claude_dir / "offsets.json"

    results = discover_sessions(
        config,
        state,
        offsets_path=offsets_path,
        history_path=sample_history,
    )

    assert len(results) == 4  # 4 entries in sample_history
    session_ids = {r[0] for r in results}
    assert "sess-001" in session_ids
    assert "sess-002" in session_ids

    # State updated
    assert "sess-001" in state.sessions_tracked
    assert "sess-002" in state.sessions_tracked
    assert state.session_projects["sess-001"] == "/Users/test/proj-a"


def test_discover_sessions_incremental(tmp_claude_dir: Path, sample_history: Path):
    config = ScribeWatchConfig(claude_dir=tmp_claude_dir)
    state = WatchState()
    offsets_path = tmp_claude_dir / "offsets.json"

    # First poll
    discover_sessions(config, state, offsets_path=offsets_path, history_path=sample_history)

    # Second poll with no new data
    results = discover_sessions(
        config,
        state,
        offsets_path=offsets_path,
        history_path=sample_history,
    )
    assert len(results) == 0


def test_discover_sessions_new_data(tmp_claude_dir: Path, sample_history: Path):
    config = ScribeWatchConfig(claude_dir=tmp_claude_dir)
    state = WatchState()
    offsets_path = tmp_claude_dir / "offsets.json"

    # First poll
    discover_sessions(config, state, offsets_path=offsets_path, history_path=sample_history)

    # Append new entry
    with sample_history.open("a") as f:
        f.write(
            json.dumps(
                {
                    "display": "new message",
                    "timestamp": 1776010000000,
                    "project": "/Users/test/proj-c",
                    "sessionId": "sess-003",
                }
            )
            + "\n"
        )

    results = discover_sessions(
        config,
        state,
        offsets_path=offsets_path,
        history_path=sample_history,
    )
    assert len(results) == 1
    assert results[0][0] == "sess-003"


def test_discover_sessions_nonexistent_history(tmp_claude_dir: Path):
    config = ScribeWatchConfig(claude_dir=tmp_claude_dir)
    state = WatchState()
    results = discover_sessions(
        config,
        state,
        history_path=tmp_claude_dir / "nonexistent.jsonl",
    )
    assert results == []


# -- find_idle_sessions --------------------------------------------------------


def test_find_idle_sessions():
    now = time.time()
    state = WatchState(
        sessions_tracked={
            "sess-old": now - 700,  # 11+ minutes ago
            "sess-recent": now - 60,  # 1 minute ago
        },
        session_projects={
            "sess-old": "/test/proj-a",
            "sess-recent": "/test/proj-b",
        },
    )

    idle = find_idle_sessions(state, idle_minutes=10)
    assert len(idle) == 1
    assert idle[0][0] == "sess-old"


def test_find_idle_sessions_excludes_analyzed():
    now = time.time()
    state = WatchState(
        sessions_tracked={"sess-old": now - 700},
        sessions_analyzed=["sess-old"],
        session_projects={"sess-old": "/test/proj"},
    )

    idle = find_idle_sessions(state, idle_minutes=10)
    assert len(idle) == 0


# -- process_session -----------------------------------------------------------


def test_process_session_with_insights(sample_session: tuple[str, str, Path], tmp_path: Path):
    session_id, project_path, claude_dir = sample_session
    store = Store(db_path=tmp_path / "recall.db")

    activity = process_session(
        session_id,
        project_path,
        store,
        claude_dir=claude_dir,
    )

    assert activity.session_id == session_id
    assert activity.project == "proj-a"
    assert activity.insights_generated > 0
    assert activity.insights_added > 0
    assert activity.analysis_duration_ms >= 0
    store.close()


def test_process_session_nonexistent(tmp_claude_dir: Path, tmp_path: Path):
    store = Store(db_path=tmp_path / "recall.db")
    activity = process_session(
        "nonexistent",
        "/fake/path",
        store,
        claude_dir=tmp_claude_dir,
    )
    assert activity.insights_generated == 0
    assert activity.insights_added == 0
    store.close()


def test_process_session_dedup_on_reprocess(sample_session: tuple[str, str, Path], tmp_path: Path):
    session_id, project_path, claude_dir = sample_session
    store = Store(db_path=tmp_path / "recall.db")

    # First process
    act1 = process_session(session_id, project_path, store, claude_dir=claude_dir)

    # Second process -- should dedup most entries
    act2 = process_session(session_id, project_path, store, claude_dir=claude_dir)

    assert act2.insights_added <= act1.insights_added
    store.close()


# -- watch_once ----------------------------------------------------------------


def test_watch_once_end_to_end(
    tmp_claude_dir: Path,
    sample_history: Path,
    sample_session: tuple[str, str, Path],
    tmp_path: Path,
):
    config = ScribeWatchConfig(
        claude_dir=tmp_claude_dir,
        idle_minutes=0,  # All sessions are "idle" immediately
    )
    store = Store(db_path=tmp_path / "recall.db")
    offsets_path = tmp_path / "offsets.json"
    state_path = tmp_path / "state.json"

    activities = watch_once(
        config,
        store,
        offsets_path=offsets_path,
        state_path=state_path,
        history_path=sample_history,
    )

    # sess-001 has a session JSONL, sess-002 does not
    processed = [a for a in activities if a.insights_generated > 0]
    assert len(processed) >= 1

    # State persisted
    state = load_state(state_path)
    assert len(state.sessions_analyzed) > 0
    store.close()
