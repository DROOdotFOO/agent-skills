"""Data models for scribe session analysis and insight extraction."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field
from recall.models import EntryType


class InsightType(str, Enum):
    """Extended classification beyond recall's EntryType.

    Scribe detects richer categories but maps them to recall's EntryType for storage.
    """

    DECISION = "decision"
    PATTERN = "pattern"
    GOTCHA = "gotcha"
    INSIGHT = "insight"
    LINK = "link"
    CORRECTION = "correction"  # User correcting Claude -> stored as gotcha
    PREFERENCE = "preference"  # "I prefer X" -> stored as decision
    REPEATED_FAILURE = "repeated_failure"  # Same error across sessions -> stored as gotcha


INSIGHT_TO_ENTRY_TYPE: dict[InsightType, EntryType] = {
    InsightType.DECISION: EntryType.DECISION,
    InsightType.PATTERN: EntryType.PATTERN,
    InsightType.GOTCHA: EntryType.GOTCHA,
    InsightType.INSIGHT: EntryType.INSIGHT,
    InsightType.LINK: EntryType.LINK,
    InsightType.CORRECTION: EntryType.GOTCHA,
    InsightType.PREFERENCE: EntryType.DECISION,
    InsightType.REPEATED_FAILURE: EntryType.GOTCHA,
}


class ToolCall(BaseModel):
    """A single tool invocation extracted from an assistant message."""

    name: str
    input: dict = Field(default_factory=dict)
    timestamp: str | None = None


class SessionMessage(BaseModel):
    """A parsed message from a session JSONL file."""

    type: str  # user, assistant, system, file-history-snapshot, attachment
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    timestamp: str | None = None
    uuid: str | None = None


class SessionAnalysis(BaseModel):
    """Structured analysis of a complete Claude Code session."""

    session_id: str
    project: str | None = None
    project_path: str | None = None
    duration_seconds: float | None = None
    message_count: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0
    tool_usage: dict[str, int] = Field(default_factory=dict)
    files_read: list[str] = Field(default_factory=list)
    files_edited: list[str] = Field(default_factory=list)
    files_created: list[str] = Field(default_factory=list)
    commands_run: list[str] = Field(default_factory=list)
    failed_commands: list[str] = Field(default_factory=list)
    user_texts: list[str] = Field(default_factory=list)
    corrections: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)


class ScribeActivity(BaseModel):
    """Activity log entry written to activity.jsonl after processing a session."""

    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_id: str
    project: str | None = None
    insights_generated: int = 0
    insights_added: int = 0
    insights_deduplicated: int = 0
    analysis_duration_ms: int = 0


class WatchState(BaseModel):
    """Persistent state for the watch command."""

    sessions_tracked: dict[str, float] = Field(default_factory=dict)
    sessions_analyzed: list[str] = Field(default_factory=list)
    session_projects: dict[str, str] = Field(default_factory=dict)
    last_poll_ts: float = 0.0
