"""Data models for digest items and results."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Item(BaseModel):
    """A single item fetched from a platform adapter."""

    source: str = Field(description="Platform identifier: hn, github, reddit, etc.")
    title: str
    url: str
    author: str | None = None
    timestamp: datetime
    engagement: int = Field(description="Normalized engagement score")
    summary: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict, description="Source-specific data")

    def dedupe_key(self) -> str:
        """A key that should match across platforms for the same story."""
        return self.url.rstrip("/").lower()


class DigestRequest(BaseModel):
    topic: str
    days: int = 30
    platforms: list[str] = Field(default_factory=list)
    max_items_per_platform: int = 50


class DigestResult(BaseModel):
    topic: str
    days: int
    items: list[Item]
    narrative: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
