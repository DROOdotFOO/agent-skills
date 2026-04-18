"""Shared data models for agent-skills agents."""

from __future__ import annotations

from enum import Enum


class AlertSeverity(str, Enum):
    """Severity levels for agent alerts."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
