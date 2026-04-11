"""Core data models for patchbot."""

from enum import Enum

from pydantic import BaseModel


class Ecosystem(str, Enum):
    ELIXIR = "elixir"
    RUST = "rust"
    NODE = "node"
    GO = "go"
    PYTHON = "python"


class Dependency(BaseModel):
    """A single dependency with version info."""

    name: str
    current_version: str
    latest_version: str | None = None
    ecosystem: Ecosystem


class UpdatePlan(BaseModel):
    """Plan for updating dependencies in one ecosystem."""

    ecosystem: Ecosystem
    dependencies: list[Dependency]
    update_command: str
    test_command: str


class UpdateResult(BaseModel):
    """Result of executing an update plan."""

    plan: UpdatePlan
    success: bool
    test_passed: bool
    pr_url: str | None = None
