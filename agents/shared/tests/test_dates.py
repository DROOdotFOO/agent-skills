"""Unit tests for shared.dates helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from shared.dates import cutoff_datetime, parse_date_utc, parse_iso_utc, since_date

# ----------------------------------------------------------------------
# parse_iso_utc
# ----------------------------------------------------------------------


def test_parse_iso_utc_z_suffix():
    assert parse_iso_utc("2024-06-15T12:30:00Z") == datetime(
        2024, 6, 15, 12, 30, 0, tzinfo=timezone.utc
    )


def test_parse_iso_utc_offset():
    assert parse_iso_utc("2024-06-15T12:30:00+00:00") == datetime(
        2024, 6, 15, 12, 30, 0, tzinfo=timezone.utc
    )


def test_parse_iso_utc_naive_tags_utc():
    assert parse_iso_utc("2024-06-15") == datetime(2024, 6, 15, tzinfo=timezone.utc)


def test_parse_iso_utc_none_for_none():
    assert parse_iso_utc(None) is None


def test_parse_iso_utc_none_for_empty():
    assert parse_iso_utc("") is None


def test_parse_iso_utc_none_for_unparseable():
    assert parse_iso_utc("not-a-date") is None


def test_parse_iso_utc_none_for_non_string():
    assert parse_iso_utc(12345) is None  # type: ignore[arg-type]


# ----------------------------------------------------------------------
# parse_date_utc
# ----------------------------------------------------------------------


def test_parse_date_utc_default_iso():
    assert parse_date_utc("2024-06-15") == datetime(2024, 6, 15, tzinfo=timezone.utc)


def test_parse_date_utc_custom_format():
    assert parse_date_utc("2024/06/15", formats=("%Y/%m/%d",)) == datetime(
        2024, 6, 15, tzinfo=timezone.utc
    )


def test_parse_date_utc_multi_format_falls_through():
    """Tries each format in order; first match wins."""
    assert parse_date_utc("2024-06", formats=("%Y-%m-%d", "%Y-%m")) == datetime(
        2024, 6, 1, tzinfo=timezone.utc
    )


def test_parse_date_utc_none_for_none():
    assert parse_date_utc(None) is None


def test_parse_date_utc_none_for_unparseable():
    assert parse_date_utc("not-a-date") is None


# ----------------------------------------------------------------------
# since_date / cutoff_datetime
# ----------------------------------------------------------------------


def test_since_date_default_iso():
    s = since_date(30)
    assert s is not None
    assert len(s) == 10
    assert s[4] == "-"


def test_since_date_slash_format():
    s = since_date(30, fmt="%Y/%m/%d")
    assert s is not None
    assert s[4] == "/"


def test_since_date_none_for_zero():
    assert since_date(0) is None


def test_since_date_none_for_negative():
    assert since_date(-1) is None


def test_since_date_is_days_ago():
    """A 30-day window produces a date in [30, 31) days back."""
    s = since_date(30)
    parsed = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - parsed
    assert timedelta(days=30) <= delta < timedelta(days=31)


def test_cutoff_datetime_returns_utc():
    c = cutoff_datetime(7)
    assert c is not None
    assert c.tzinfo == timezone.utc


def test_cutoff_datetime_none_for_zero():
    assert cutoff_datetime(0) is None


def test_cutoff_datetime_none_for_negative():
    assert cutoff_datetime(-1) is None
