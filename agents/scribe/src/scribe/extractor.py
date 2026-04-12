"""Insight extraction and classification from session analysis."""

from __future__ import annotations

import re

from recall.extract import classify_entry_type, extract_tags
from recall.models import Entry, EntryType

from scribe.models import INSIGHT_TO_ENTRY_TYPE, InsightType, SessionAnalysis

# Correction patterns (user correcting Claude)
_CORRECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^no[,.]?\s", re.IGNORECASE),
    re.compile(r"\bthat'?s\s+(not\s+)?(wrong|incorrect)\b", re.IGNORECASE),
    re.compile(r"\bnot\s+what\s+I\s+(meant|asked|wanted)\b", re.IGNORECASE),
    re.compile(r"\bactually[,.]?\s", re.IGNORECASE),
    re.compile(r"\btry\s+again\b", re.IGNORECASE),
    re.compile(r"\bundo\s+that\b", re.IGNORECASE),
]

# Preference patterns (user stating preferences)
_PREFERENCE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bI\s+prefer\b", re.IGNORECASE),
    re.compile(r"\balways\s+use\b", re.IGNORECASE),
    re.compile(r"\bnever\s+use\b", re.IGNORECASE),
    re.compile(r"\bfrom\s+now\s+on\b", re.IGNORECASE),
    re.compile(r"\bmy\s+(convention|preference|style)\s+is\b", re.IGNORECASE),
    re.compile(r"\bdon'?t\s+ever\b", re.IGNORECASE),
]


def classify_insight_type(text: str) -> InsightType:
    """Classify text into an InsightType, checking scribe-specific patterns first.

    Priority: correction > preference > recall's classify_entry_type mapping.
    """
    for pattern in _CORRECTION_PATTERNS:
        if pattern.search(text):
            return InsightType.CORRECTION

    for pattern in _PREFERENCE_PATTERNS:
        if pattern.search(text):
            return InsightType.PREFERENCE

    # Fall back to recall's classifier and map to InsightType
    recall_type = classify_entry_type(text)
    return InsightType(recall_type.value)


def extract_insights(analysis: SessionAnalysis) -> list[Entry]:
    """Generate recall Entry objects from a SessionAnalysis.

    Sources of insights:
    1. User corrections -> gotcha entries
    2. User preferences -> decision entries
    3. Pattern-matching on user texts (enhanced classify)
    4. Tool usage pattern insights
    """
    entries: list[Entry] = []
    source = f"scribe:{analysis.session_id}"

    # 1. Corrections
    for text in analysis.corrections:
        insight_type = InsightType.CORRECTION
        entry_type = INSIGHT_TO_ENTRY_TYPE[insight_type]
        tags = extract_tags(text)
        tags.append("scribe:correction")

        entries.append(
            Entry(
                content=text,
                entry_type=entry_type,
                project=analysis.project,
                tags=sorted(set(tags)),
                source=source,
            )
        )

    # 2. Preferences
    for text in analysis.preferences:
        insight_type = InsightType.PREFERENCE
        entry_type = INSIGHT_TO_ENTRY_TYPE[insight_type]
        tags = extract_tags(text)
        tags.append("scribe:preference")

        entries.append(
            Entry(
                content=text,
                entry_type=entry_type,
                project=analysis.project,
                tags=sorted(set(tags)),
                source=source,
            )
        )

    # 3. Pattern-matching on remaining user texts
    seen_texts = set(analysis.corrections + analysis.preferences)
    for text in analysis.user_texts:
        if text in seen_texts:
            continue
        if len(text) < 20:
            continue

        insight_type = classify_insight_type(text)
        # Only keep non-generic insights
        if insight_type == InsightType.INSIGHT:
            # recall's classify_entry_type returns INSIGHT as default --
            # skip these to avoid noise
            continue

        entry_type = INSIGHT_TO_ENTRY_TYPE[insight_type]
        tags = extract_tags(text)
        tags.append(f"scribe:{insight_type.value}")

        entries.append(
            Entry(
                content=text,
                entry_type=entry_type,
                project=analysis.project,
                tags=sorted(set(tags)),
                source=source,
            )
        )

    # 4. Tool usage pattern insights
    entries.extend(_tool_pattern_insights(analysis))

    return entries


def _tool_pattern_insights(analysis: SessionAnalysis) -> list[Entry]:
    """Generate insights from notable tool usage patterns."""
    entries: list[Entry] = []
    source = f"scribe:{analysis.session_id}"
    usage = analysis.tool_usage

    total_tools = sum(usage.values())
    if total_tools < 5:
        return entries

    # Heavy Edit session with no tests run
    edit_count = usage.get("Edit", 0) + usage.get("Write", 0)
    has_test_cmd = any(
        "test" in cmd or "pytest" in cmd or "mix test" in cmd for cmd in analysis.commands_run
    )

    if edit_count >= 5 and not has_test_cmd:
        entries.append(
            Entry(
                content=(
                    f"Session {analysis.session_id} in {analysis.project}: "
                    f"{edit_count} file edits with no test commands run. "
                    "Consider adding test verification after edits."
                ),
                entry_type=EntryType.PATTERN,
                project=analysis.project,
                tags=["scribe:tool-pattern", "testing"],
                source=source,
            )
        )

    # Repeated Read without Edit = exploration session
    read_count = usage.get("Read", 0)
    if read_count >= 10 and edit_count == 0:
        entries.append(
            Entry(
                content=(
                    f"Session {analysis.session_id} in {analysis.project}: "
                    f"exploration session ({read_count} reads, 0 edits). "
                    "Pure investigation / code review."
                ),
                entry_type=EntryType.PATTERN,
                project=analysis.project,
                tags=["scribe:tool-pattern", "exploration"],
                source=source,
            )
        )

    return entries
