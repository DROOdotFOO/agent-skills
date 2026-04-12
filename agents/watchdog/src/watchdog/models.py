"""Data models for watchdog health checks."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]


class Status(str, Enum):
    """Health check result status."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class CheckResult(BaseModel):
    """Result of a single health check."""

    check_name: str
    status: Status
    message: str
    details: str = ""

    @property
    def icon(self) -> str:
        return {"pass": "[+]", "warn": "[~]", "fail": "[-]"}[self.status.value]


class RepoHealth(BaseModel):
    """Aggregated health for one repository."""

    repo: str
    checks: list[CheckResult] = Field(default_factory=list)
    scanned_at: datetime = Field(default_factory=datetime.now)

    @property
    def overall_status(self) -> Status:
        if any(c.status == Status.FAIL for c in self.checks):
            return Status.FAIL
        if any(c.status == Status.WARN for c in self.checks):
            return Status.WARN
        return Status.PASS


class AlertSeverity(str, Enum):
    """Severity levels for watchdog alerts (aligned with sentinel/digest)."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class WatchdogAlert(BaseModel):
    """A persisted alert derived from a WARN or FAIL check result."""

    repo: str
    check_name: str
    status: Status
    severity: AlertSeverity
    message: str
    details: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RepoConfig(BaseModel):
    """Configuration for a single repo to monitor."""

    name: str
    path: str | None = None


class Thresholds(BaseModel):
    """Configurable thresholds for checks."""

    stale_pr_days: int = 14
    stale_issue_days: int = 30


class Schedule(BaseModel):
    """Watch schedule configuration."""

    interval_minutes: int = 60


class WatchConfig(BaseModel):
    """Top-level configuration loaded from watchdog.toml."""

    repos: list[RepoConfig] = Field(default_factory=list)
    thresholds: Thresholds = Field(default_factory=Thresholds)
    schedule: Schedule = Field(default_factory=Schedule)

    @classmethod
    def from_toml(cls, path: Path) -> WatchConfig:
        """Load configuration from a TOML file."""
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls(**data)

    @classmethod
    def from_repos(cls, repos: list[str]) -> WatchConfig:
        """Create config from a list of repo names (owner/repo)."""
        return cls(repos=[RepoConfig(name=r) for r in repos])
