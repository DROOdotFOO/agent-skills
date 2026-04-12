"""AARTS Level 2 hooks for prepper.

PreMemoryRead: scans recall entries before they enter briefing sections.
Strips entries with injection patterns and flags auto-sourced entries
with provenance markers.
"""

from __future__ import annotations

import re
import sys
from typing import Any

# Injection patterns (standalone copy -- agents don't cross-import).
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

# Sources that indicate automated (non-manual) entry creation.
AUTO_SOURCE_PREFIXES = ("digest:", "extract:")


def _scan_text(text: str) -> str | None:
    """Check text for injection patterns. Returns description if found, else None."""
    for pattern, description in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return description
    return None


def is_auto_sourced(entry: Any) -> bool:
    """Check if a recall entry was created by automated processes."""
    source = getattr(entry, "source", None) or ""
    return any(source.startswith(prefix) for prefix in AUTO_SOURCE_PREFIXES)


def pre_memory_read(entries: list[Any]) -> list[Any]:
    """Scan recall entries before they enter briefing sections.

    Strips entries whose content contains injection patterns.
    Returns the filtered list. Logs removals to stderr.
    """
    clean: list[Any] = []
    for entry in entries:
        content = getattr(entry, "content", "")
        reason = _scan_text(content)
        if reason is not None:
            source = getattr(entry, "source", "unknown")
            print(
                f"[HOOK] PreMemoryRead: stripped entry from {source} ({reason}): {content[:80]}",
                file=sys.stderr,
            )
        else:
            clean.append(entry)
    return clean
