"""Date and date-window helpers shared across agents.

Used by digest adapters, sentinel monitor, scribe analyzer, and watchdog
checks -- anywhere a timestamp comes back from an API as an ISO 8601
string or a ``YYYY-MM-DD`` date.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def parse_iso_utc(value: str | None) -> datetime | None:
    """Parse a flexible ISO 8601 timestamp via ``datetime.fromisoformat``.

    Accepts full timestamps with timezones, trailing ``Z``, naive dates, etc.
    Tags naive results UTC. Returns ``None`` for missing or unparseable input.

    Use this when the API can return either ``"2024-06-15"`` or
    ``"2024-06-15T12:30:00Z"``.
    """
    if not value or not isinstance(value, str):
        return None
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def parse_date_utc(
    value: str | None,
    formats: tuple[str, ...] = ("%Y-%m-%d",),
) -> datetime | None:
    """Parse a date string via ``strptime`` against one or more formats.

    Returns a UTC-tagged datetime on success, ``None`` for missing or
    unparseable input. Tries each format in order; first match wins.

    Use the default for the common ``YYYY-MM-DD`` API shape. Pass a custom
    tuple for slash-separated dates (``"%Y/%m/%d"``, e.g. PubMed) or
    multi-precision fallbacks (``("%Y-%m-%d", "%Y-%m", "%Y")``, e.g.
    ClinicalTrials).
    """
    if not value or not isinstance(value, str):
        return None
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def since_date(days: int, fmt: str = "%Y-%m-%d") -> str | None:
    """Compute the lower-bound date string ``days`` ago, in ``fmt``.

    Returns ``None`` for ``days <= 0`` so callers can omit the filter
    entirely when no time window applies. Default format is ISO; pass
    ``"%Y/%m/%d"`` for PubMed-style slash dates.
    """
    if days <= 0:
        return None
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return cutoff.strftime(fmt)


def cutoff_datetime(days: int) -> datetime | None:
    """Compute the lower-bound datetime ``days`` ago, UTC-tagged.

    Returns ``None`` for ``days <= 0``. Companion to ``since_date`` for
    cases where the caller wants to compare against parsed datetimes
    (e.g. client-side date filtering when the API has no native filter).
    """
    if days <= 0:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)
