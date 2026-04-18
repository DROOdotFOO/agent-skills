"""AARTS Level 2 hooks for prepper.

PreMemoryRead: scans recall entries before they enter briefing sections.
Strips entries with injection patterns and flags auto-sourced entries
with provenance markers.
"""

from __future__ import annotations

import re
import sys
from typing import Any

from shared.hooks import INJECTION_PATTERNS

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
