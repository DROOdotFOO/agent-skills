"""Data models for prepper briefings."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BriefingSection(BaseModel):
    """A single section of a project briefing."""

    title: str
    content: str
    priority: Priority = Priority.MEDIUM


class Briefing(BaseModel):
    """A complete project briefing assembled from multiple sections."""

    project_name: str
    sections: list[BriefingSection] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
