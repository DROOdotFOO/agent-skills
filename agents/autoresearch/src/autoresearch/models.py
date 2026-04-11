"""Data models for autoresearch experiments."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Direction(str, Enum):
    LOWER = "lower"
    HIGHER = "higher"


class Status(str, Enum):
    KEEP = "keep"
    DISCARD = "discard"
    CRASH = "crash"
    BASELINE = "baseline"


class ExperimentConfig(BaseModel):
    """Configuration for an experiment session."""

    name: str = Field(description="Short experiment name (used as branch suffix)")
    objective: str = Field(description="What we're optimizing, in plain English")
    metric_name: str = Field(description="Name of the primary metric")
    metric_unit: str = Field(
        default="", description="Unit of the metric (e.g. 'ms', 'gas', 'constraints')"
    )
    direction: Direction = Field(description="Whether lower or higher is better")
    verify_command: str = Field(description="Shell command to run the experiment")
    metric_pattern: str = Field(
        default=r"METRIC\s+(\S+)=(\S+)",
        description="Regex to extract metric from verify command output. Group 1=name, group 2=value.",
    )
    mutable_files: list[str] = Field(
        default_factory=list,
        description="Files the agent is allowed to modify",
    )
    readonly_files: list[str] = Field(
        default_factory=list,
        description="Files the agent should read but never modify",
    )
    time_budget_seconds: int = Field(
        default=300,
        description="Max wall-clock seconds per run (default 5 min)",
    )
    guard_command: str | None = Field(
        default=None,
        description="Optional safety command that must pass for changes to be kept (e.g. 'cargo test')",
    )


class RunResult(BaseModel):
    """Result of a single experiment run."""

    run: int
    commit: str = ""
    metric: float | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    status: Status
    description: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    duration_seconds: float = 0.0


class ExperimentState(BaseModel):
    """Full state of an experiment session."""

    config: ExperimentConfig
    results: list[RunResult] = Field(default_factory=list)
    best_metric: float | None = None
    best_run: int | None = None
    current_run: int = 0

    @property
    def is_better(self) -> bool:
        """Check if the latest run improved on the best."""
        if not self.results or self.best_metric is None:
            return False
        latest = self.results[-1]
        if latest.metric is None:
            return False
        if self.config.direction == Direction.LOWER:
            return latest.metric < self.best_metric
        return latest.metric > self.best_metric

    def update_best(self) -> None:
        """Update best_metric and best_run from results."""
        for r in self.results:
            if r.metric is None or r.status == Status.CRASH:
                continue
            if (
                self.best_metric is None
                or self.config.direction == Direction.LOWER
                and r.metric < self.best_metric
                or self.config.direction == Direction.HIGHER
                and r.metric > self.best_metric
            ):
                self.best_metric = r.metric
                self.best_run = r.run
