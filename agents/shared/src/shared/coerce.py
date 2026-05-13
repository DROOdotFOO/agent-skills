"""Value-coercion helpers shared across agents.

Generic shape concerns: ``None`` / string / numeric coercion, plus the
"First Author et al." rendering used wherever an API returns an authors
list. API-specific extraction (nested fields, fallback chains) stays at
the caller; pass clean names into ``format_authors_etal``.
"""

from __future__ import annotations


def coerce_int(value: object) -> int:
    """Convert any int/str/numeric-string to int. ``None`` or unparseable -> 0.

    Used wherever the API may return ``None``, a number, or a stringified
    number for a count field (citations, page views, enrollments, etc.).
    """
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def coerce_float(value: object) -> float | None:
    """Convert any float/str/numeric-string to float. ``None`` or unparseable -> None.

    Returns ``None`` (not ``0.0``) for unparseable input so callers can
    distinguish "not yet scored" (e.g. fwci/RCR for too-new papers) from
    "below average" (a real 0.0 or negative value).
    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def format_authors_etal(names: list[str]) -> str | None:
    """Render a name list as ``"Name"`` (single) or ``"Name et al."`` (multi).

    Filters out falsy / non-string entries defensively. Returns ``None`` if
    nothing usable remains.

    Adapters should extract the raw name list (from whatever nested shape
    their API uses), then pass the list to this helper.
    """
    clean = [n for n in names if n and isinstance(n, str)]
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    return f"{clean[0]} et al."
