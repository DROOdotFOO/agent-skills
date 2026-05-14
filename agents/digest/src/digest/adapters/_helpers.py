"""Adapter helper re-exports.

The implementations live in ``agents/shared/src/shared/`` so sentinel,
scribe, watchdog, and other agents can reuse them. This module re-exports
under the names digest adapters originally imported, so adapter source
files don't need to know whether the helper lives in digest or shared.
"""

from __future__ import annotations

from shared.coerce import coerce_float, coerce_int, format_authors_etal
from shared.dates import (
    cutoff_datetime,
    parse_date_utc,
    parse_iso_utc,
    since_date,
)
from shared.http import fetch_json, fetch_text

__all__ = [
    "coerce_float",
    "coerce_int",
    "cutoff_datetime",
    "fetch_json",
    "fetch_text",
    "format_authors_etal",
    "parse_date_utc",
    "parse_iso_utc",
    "since_date",
]
