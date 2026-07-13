"""Pydantic models for Regen incidents, alerts, and correlation output.

Mirrors the Regen v1.0.0 REST DTOs (``IncidentResponse`` /
``IncidentDetailResponse`` / ``AlertSummary`` in
``backend/internal/api/handlers/dto``). Status and severity are stored as plain
strings for forward-compatibility with values the enums below don't yet know;
the enums provide the canonical vocabulary for CLI/tool filters.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IncidentStatus(str, Enum):
    """Incident lifecycle states accepted by Regen's list filter + PATCH."""

    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CANCELED = "canceled"


class Severity(str, Enum):
    """Incident severities accepted by Regen's list filter + PATCH."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertSummary(BaseModel):
    """A minimal alert as embedded in an incident detail response.

    ``labels`` is the correlation join point: the SigNoz webhook lands
    ``service.name`` / ``chain`` / ``role`` / ``intent_id`` here.
    """

    id: str = ""
    title: str = ""
    source: str = ""
    severity: str = ""
    status: str = ""
    labels: dict[str, Any] = Field(default_factory=dict)
    received_at: datetime | None = None


class TimelineEntry(BaseModel):
    """A single incident timeline event."""

    id: str = ""
    timestamp: datetime | None = None
    type: str = ""
    actor_type: str = ""
    actor_name: str = ""
    content: dict[str, Any] = Field(default_factory=dict)


class Incident(BaseModel):
    """A Regen incident (list/summary shape)."""

    id: str = ""
    incident_number: int = 0
    title: str = ""
    slug: str = ""
    status: str = ""
    severity: str = ""
    summary: str = ""
    group_key: str | None = None
    created_at: datetime | None = None
    triggered_at: datetime | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    ai_summary: str | None = None
    ai_enabled: bool = False
    commander_name: str = ""


class IncidentDetail(Incident):
    """An incident with its linked alerts and timeline."""

    alerts: list[AlertSummary] = Field(default_factory=list)
    timeline: list[TimelineEntry] = Field(default_factory=list)


class CorrelationKeys(BaseModel):
    """Join keys extracted from an incident, ready to query the SigNoz MCP."""

    incident_id: str
    incident_number: int
    title: str
    status: str
    severity: str
    service_names: list[str] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
    window_start: datetime | None = None
    window_end: datetime | None = None
    signoz_hint: str = ""
