"""AARTS Level 2 hooks for digest.

PostToolUse: scans adapter response items for injection patterns before
they reach dedup/ranking/synthesis. Strips poisoned items rather than
crashing the pipeline.
"""

from __future__ import annotations

import re
import sys
from typing import Any

from digest.models import Item

# Patterns that indicate prompt injection attempts in adapter responses.
# Duplicated from recall.hooks (agents are standalone, no cross-imports).
INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"<\s*system\s*>", "XML system tag"),
    (r"<\s*/\s*system\s*>", "XML system close tag"),
    (r"<\s*instructions?\s*>", "XML instructions tag"),
    (r"<\s*tool_use\s*>", "XML tool_use tag"),
    (r"\[INST\]", "instruction delimiter"),
    (r"<<\s*SYS\s*>>", "Llama system delimiter"),
    (r"(?i)ignore\s+(all\s+)?previous\s+instructions?", "instruction override attempt"),
    (r"(?i)you\s+are\s+now\s+(?:a|an)\b", "role reassignment attempt"),
    (
        r"(?i)forget\s+(?:all\s+)?(?:your\s+)?(?:previous\s+)?instructions?",
        "instruction override attempt",
    ),
    (r"(?i)new\s+system\s+prompt", "system prompt injection"),
]


def _scan_text(text: str) -> str | None:
    """Check text for injection patterns. Returns description if found, else None."""
    for pattern, description in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return description
    return None


def _scan_raw(raw: dict[str, Any]) -> str | None:
    """Recursively scan raw dict string values for injection patterns."""
    for value in raw.values():
        if isinstance(value, str):
            found = _scan_text(value)
            if found:
                return found
        elif isinstance(value, dict):
            found = _scan_raw(value)
            if found:
                return found
    return None


def _check_item(item: Item) -> str | None:
    """Scan an Item's title, url, and raw dict for injection. Returns reason or None."""
    for field in (item.title, item.url):
        found = _scan_text(field)
        if found:
            return found
    if item.raw:
        found = _scan_raw(item.raw)
        if found:
            return found
    return None


def post_tool_use(items: list[Item]) -> list[Item]:
    """Scan adapter response items and strip those containing injection patterns.

    Returns a new list with poisoned items removed. Logs removals to stderr.
    """
    clean: list[Item] = []
    for item in items:
        reason = _check_item(item)
        if reason is not None:
            print(
                f"[HOOK] PostToolUse: stripped item from {item.source} "
                f"({reason}): {item.title[:80]}",
                file=sys.stderr,
            )
        else:
            clean.append(item)
    return clean


def sanitize_context(text: str) -> str:
    """Strip lines containing injection patterns from recall context text.

    Returns sanitized text with offending lines removed.
    """
    if not text:
        return text

    clean_lines: list[str] = []
    for line in text.splitlines():
        found = _scan_text(line)
        if found is not None:
            print(
                f"[HOOK] PostToolUse: stripped context line ({found}): {line[:80]}",
                file=sys.stderr,
            )
        else:
            clean_lines.append(line)
    return "\n".join(clean_lines)
