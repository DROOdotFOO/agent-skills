"""Extract decisions and insights from Claude Code session logs."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from recall.models import Entry, EntryType

DEFAULT_HISTORY_PATH = Path.home() / ".claude" / "history.jsonl"

# Patterns mapped to entry types, checked in priority order.
_DECISION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\blet'?s go with\b", re.IGNORECASE),
    re.compile(r"\bdecided to\b", re.IGNORECASE),
    re.compile(r"\bwe should\b", re.IGNORECASE),
    re.compile(r"\bthe approach is\b", re.IGNORECASE),
]

_GOTCHA_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bdon'?t use\b", re.IGNORECASE),
    re.compile(r"\bavoid\b", re.IGNORECASE),
    re.compile(r"\bnever\b", re.IGNORECASE),
    re.compile(r"\balways\b", re.IGNORECASE),
    re.compile(r"\bmake sure to\b", re.IGNORECASE),
    re.compile(r"\bthe problem was\b", re.IGNORECASE),
    re.compile(r"\broot cause\b", re.IGNORECASE),
    re.compile(r"\bthe fix is\b", re.IGNORECASE),
    re.compile(r"\bturns out\b", re.IGNORECASE),
]

_PATTERN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bremember to\b", re.IGNORECASE),
]

_INSIGHT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bnote:", re.IGNORECASE),
    re.compile(r"\bimportant:", re.IGNORECASE),
]

# Technical terms for auto-tagging.
_TAG_TERMS: list[str] = [
    "rust",
    "python",
    "typescript",
    "javascript",
    "elixir",
    "go",
    "lua",
    "bash",
    "shell",
    "docker",
    "kubernetes",
    "k8s",
    "postgres",
    "sqlite",
    "redis",
    "git",
    "ci",
    "cd",
    "api",
    "graphql",
    "grpc",
    "rest",
    "http",
    "ssl",
    "tls",
    "auth",
    "oauth",
    "jwt",
    "css",
    "html",
    "react",
    "nextjs",
    "node",
    "npm",
    "pnpm",
    "nix",
    "flake",
    "chezmoi",
    "terraform",
    "aws",
    "gcp",
    "azure",
    "solidity",
    "foundry",
    "hardhat",
    "noir",
    "zk",
    "mcp",
    "fastmcp",
    "pydantic",
    "sqlalchemy",
    "django",
    "flask",
    "fastapi",
    "async",
    "concurrency",
    "performance",
    "security",
    "testing",
    "migration",
    "refactor",
    "deploy",
    "debug",
    "cache",
    "queue",
    "websocket",
]

_TAG_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in _TAG_TERMS) + r")\b",
    re.IGNORECASE,
)


def classify_entry_type(text: str) -> EntryType:
    """Classify a message into an entry type based on keyword patterns.

    Priority order: decision > gotcha > pattern > insight.
    """
    for pattern in _DECISION_PATTERNS:
        if pattern.search(text):
            return EntryType.DECISION

    for pattern in _GOTCHA_PATTERNS:
        if pattern.search(text):
            return EntryType.GOTCHA

    for pattern in _PATTERN_PATTERNS:
        if pattern.search(text):
            return EntryType.PATTERN

    for pattern in _INSIGHT_PATTERNS:
        if pattern.search(text):
            return EntryType.INSIGHT

    return EntryType.INSIGHT


def extract_tags(text: str) -> list[str]:
    """Extract technical terms as tags from message text.

    Returns deduplicated, lowercased tags sorted alphabetically.
    """
    matches = _TAG_PATTERN.findall(text)
    return sorted(set(m.lower() for m in matches))


def _matches_any_pattern(text: str) -> bool:
    """Check whether text matches any decision-indicating pattern."""
    all_patterns = _DECISION_PATTERNS + _GOTCHA_PATTERNS + _PATTERN_PATTERNS + _INSIGHT_PATTERNS
    return any(p.search(text) for p in all_patterns)


def extract_from_logs(
    *,
    days: int = 30,
    project: str | None = None,
    history_path: Path | None = None,
) -> list[Entry]:
    """Parse Claude Code history and extract decision-indicating messages.

    Args:
        days: Only consider log entries from the last N days.
        project: Filter to entries whose project path basename matches this string.
        history_path: Path to the JSONL history file. Defaults to ~/.claude/history.jsonl.

    Returns:
        List of Entry objects extracted from the logs.
    """
    path = history_path or DEFAULT_HISTORY_PATH
    if not path.exists():
        return []

    cutoff_ts = (
        datetime.now(timezone.utc).timestamp() - (days * 86400)
    ) * 1000  # history uses millisecond timestamps

    entries: list[Entry] = []

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Skip records missing required fields.
            display = record.get("display")
            timestamp = record.get("timestamp")
            if not display or not isinstance(display, str) or timestamp is None:
                continue

            # Filter by date range.
            if timestamp < cutoff_ts:
                continue

            # Filter by project.
            record_project = record.get("project", "")
            project_basename = Path(record_project).name if record_project else ""
            if project and project_basename != project:
                continue

            # Check for decision-indicating patterns.
            if not _matches_any_pattern(display):
                continue

            session_id = record.get("sessionId", "unknown")

            entry = Entry(
                content=display,
                entry_type=classify_entry_type(display),
                project=project_basename or None,
                tags=extract_tags(display),
                source=f"session:{session_id}",
            )
            entries.append(entry)

    return entries
