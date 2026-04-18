"""Two-phase watch loop: discover sessions from history.jsonl, analyze idle ones."""

from __future__ import annotations

import json
import time
from pathlib import Path

from pydantic import BaseModel, Field
from recall.store import Store
from shared.notify import append_to_log
from shared.paths import agent_data_dir

from scribe.analyzer import analyze_session
from scribe.dedup import deduplicate
from scribe.extractor import extract_insights
from scribe.hooks import Verdict, log_hook_result, pre_scribe_write
from scribe.models import ScribeActivity, WatchState
from scribe.session_parser import parse_session

CLAUDE_DIR = Path.home() / ".claude"
HISTORY_PATH = CLAUDE_DIR / "history.jsonl"
OFFSETS_PATH = agent_data_dir("scribe") / "watch-offsets.json"
STATE_PATH = agent_data_dir("scribe") / "watch-state.json"
ACTIVITY_LOG = agent_data_dir("scribe") / "activity.jsonl"


# -- Config -------------------------------------------------------------------


class ScribeWatchConfig(BaseModel):
    """TOML-loadable config for ``scribe watch``."""

    poll_interval_minutes: int = 5
    idle_minutes: int = 10
    claude_dir: Path = Field(default_factory=lambda: CLAUDE_DIR)
    similarity_threshold: float = 0.7

    @classmethod
    def from_toml(cls, path: Path) -> ScribeWatchConfig:
        from shared.config import load_toml

        return cls(**load_toml(path))


# -- Offset tracking ----------------------------------------------------------


def load_offsets(path: Path | None = None) -> dict[str, int]:
    p = path or OFFSETS_PATH
    if p.exists():
        return json.loads(p.read_text())
    return {}


def save_offsets(offsets: dict[str, int], path: Path | None = None) -> None:
    p = path or OFFSETS_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(offsets))


# -- State persistence --------------------------------------------------------


def load_state(path: Path | None = None) -> WatchState:
    p = path or STATE_PATH
    if p.exists():
        return WatchState.model_validate_json(p.read_text())
    return WatchState()


def save_state(state: WatchState, path: Path | None = None) -> None:
    p = path or STATE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(state.model_dump_json(indent=2))


# -- Phase 1: Session discovery -----------------------------------------------


def discover_sessions(
    config: ScribeWatchConfig,
    state: WatchState,
    *,
    offsets_path: Path | None = None,
    history_path: Path | None = None,
) -> list[tuple[str, str, float]]:
    """Tail history.jsonl for new entries, update session tracking state.

    Returns list of (session_id, project_path, last_timestamp) tuples
    for sessions with new activity.
    """
    hp = history_path or (config.claude_dir / "history.jsonl")
    if not hp.exists():
        return []

    offsets = load_offsets(offsets_path)
    key = str(hp)
    current_size = hp.stat().st_size
    last_offset = offsets.get(key, 0)

    # Handle file truncation/rotation
    if current_size < last_offset:
        last_offset = 0

    if current_size <= last_offset:
        return []

    new_sessions: list[tuple[str, str, float]] = []

    with hp.open() as f:
        f.seek(last_offset)
        new_data = f.read()
        offsets[key] = f.tell()

    save_offsets(offsets, offsets_path)

    for line in new_data.strip().splitlines():
        try:
            record = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue

        session_id = record.get("sessionId")
        project = record.get("project")
        timestamp = record.get("timestamp")

        if not session_id or not project or timestamp is None:
            continue

        ts = float(timestamp) / 1000  # ms -> seconds
        state.sessions_tracked[session_id] = ts
        state.session_projects[session_id] = project
        new_sessions.append((session_id, project, ts))

    state.last_poll_ts = time.time()
    return new_sessions


# -- Phase 1b: Idle detection ------------------------------------------------


def find_idle_sessions(
    state: WatchState,
    idle_minutes: int,
) -> list[tuple[str, str]]:
    """Return (session_id, project_path) tuples for sessions idle for N minutes.

    Excludes sessions already analyzed.
    """
    cutoff = time.time() - (idle_minutes * 60)
    idle: list[tuple[str, str]] = []

    analyzed_set = set(state.sessions_analyzed)

    for sid, last_ts in state.sessions_tracked.items():
        if sid in analyzed_set:
            continue
        if last_ts < cutoff:
            project = state.session_projects.get(sid, "")
            if project:
                idle.append((sid, project))

    return idle


# -- Phase 2: Session processing ----------------------------------------------


def process_session(
    session_id: str,
    project_path: str,
    store: Store,
    *,
    claude_dir: Path | None = None,
    similarity_threshold: float = 0.7,
) -> ScribeActivity:
    """Full pipeline for one session: parse -> analyze -> extract -> dedup -> store."""
    start = time.monotonic()

    messages = parse_session(session_id, project_path, claude_dir=claude_dir)
    if not messages:
        return ScribeActivity(session_id=session_id)

    analysis = analyze_session(messages, session_id, project_path)
    candidates = extract_insights(analysis)

    # Pre-write hook filtering
    filtered: list = []
    for entry in candidates:
        result = pre_scribe_write(entry.content)
        if result.verdict == Verdict.ALLOW:
            filtered.append(entry)
        else:
            log_hook_result(result, log_all=True)

    # Dedup against recall store
    unique = deduplicate(filtered, store, similarity_threshold=similarity_threshold)

    # Write to recall
    added = 0
    for entry in unique:
        try:
            store.add(entry)
            added += 1
        except ValueError:
            # recall's pre_memory_write denied it
            pass

    elapsed_ms = int((time.monotonic() - start) * 1000)

    return ScribeActivity(
        session_id=session_id,
        project=analysis.project,
        insights_generated=len(candidates),
        insights_added=added,
        insights_deduplicated=len(filtered) - len(unique),
        analysis_duration_ms=elapsed_ms,
    )


# -- Watch loop ---------------------------------------------------------------


def watch_once(
    config: ScribeWatchConfig,
    store: Store,
    *,
    offsets_path: Path | None = None,
    state_path: Path | None = None,
    history_path: Path | None = None,
) -> list[ScribeActivity]:
    """Single poll cycle: discover sessions, find idle ones, process each."""
    state = load_state(state_path)

    discover_sessions(
        config,
        state,
        offsets_path=offsets_path,
        history_path=history_path,
    )

    idle = find_idle_sessions(state, config.idle_minutes)
    activities: list[ScribeActivity] = []

    for sid, project in idle:
        activity = process_session(
            sid,
            project,
            store,
            claude_dir=config.claude_dir,
            similarity_threshold=config.similarity_threshold,
        )
        activities.append(activity)
        state.sessions_analyzed.append(sid)

    # Persist state and activity log
    save_state(state, state_path)

    if activities:
        append_to_log(activities, ACTIVITY_LOG)

    return activities


def watch_loop(
    config: ScribeWatchConfig,
    store: Store,
    *,
    console_print: object | None = None,
) -> None:
    """Infinite poll loop. Ctrl+C to stop."""
    interval = config.poll_interval_minutes * 60
    while True:
        activities = watch_once(config, store)
        total_added = sum(a.insights_added for a in activities)
        if console_print and callable(console_print):
            console_print(
                f"Polled: {len(activities)} session(s) analyzed, "
                f"{total_added} insight(s) added to recall"
            )
        time.sleep(interval)
