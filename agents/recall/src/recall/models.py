"""Data models for recall entries."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EntryType(str, Enum):
    """Classification of captured knowledge."""

    DECISION = "decision"  # Architectural or design decision with rationale
    PATTERN = "pattern"  # Reusable approach or technique
    GOTCHA = "gotcha"  # Non-obvious pitfall or footgun
    LINK = "link"  # External resource worth remembering
    INSIGHT = "insight"  # General observation or learning


class Entry(BaseModel):
    """A single knowledge entry."""

    id: int | None = None
    content: str = Field(description="The knowledge content")
    entry_type: EntryType = Field(default=EntryType.INSIGHT)
    project: str | None = Field(default=None, description="Project this relates to")
    tags: list[str] = Field(default_factory=list)
    source: str | None = Field(
        default=None, description="Where this came from (session ID, file, manual)"
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None
    accessed_at: datetime | None = None
    access_count: int = 0

    @property
    def tags_str(self) -> str:
        return ",".join(self.tags)

    @classmethod
    def from_row(cls, row: dict) -> Entry:
        tags = [t.strip() for t in (row.get("tags") or "").split(",") if t.strip()]
        return cls(
            id=row["id"],
            content=row["content"],
            entry_type=EntryType(row["entry_type"]),
            project=row.get("project"),
            tags=tags,
            source=row.get("source"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            accessed_at=row.get("accessed_at"),
            access_count=row.get("access_count", 0),
        )


class SearchResult(BaseModel):
    """A search hit with relevance info."""

    entry: Entry
    rank: float = Field(description="FTS5 rank score (lower = more relevant)")
    snippet: str | None = Field(default=None, description="Highlighted match context")
