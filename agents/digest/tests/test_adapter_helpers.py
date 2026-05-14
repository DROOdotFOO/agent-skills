"""Unit tests for shared adapter helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from digest.adapters._helpers import (
    coerce_float,
    coerce_int,
    cutoff_datetime,
    fetch_json,
    fetch_text,
    format_authors_etal,
    parse_date_utc,
    parse_iso_utc,
    since_date,
)

# ----------------------------------------------------------------------
# coerce_int
# ----------------------------------------------------------------------


def test_coerce_int_passes_through_int():
    assert coerce_int(42) == 42


def test_coerce_int_parses_string():
    assert coerce_int("100") == 100


def test_coerce_int_zero_for_none():
    assert coerce_int(None) == 0


def test_coerce_int_zero_for_unparseable_string():
    assert coerce_int("not-a-number") == 0


def test_coerce_int_zero_for_dict():
    assert coerce_int({"foo": 1}) == 0


def test_coerce_int_truncates_float():
    assert coerce_int(3.9) == 3


# ----------------------------------------------------------------------
# coerce_float
# ----------------------------------------------------------------------


def test_coerce_float_passes_through_float():
    assert coerce_float(2.5) == 2.5


def test_coerce_float_parses_string():
    assert coerce_float("3.14") == 3.14


def test_coerce_float_promotes_int():
    assert coerce_float(7) == 7.0


def test_coerce_float_none_for_none():
    """Preserves None so callers can distinguish 'not scored' from 'below average'."""
    assert coerce_float(None) is None


def test_coerce_float_none_for_unparseable():
    assert coerce_float("garbage") is None


def test_coerce_float_none_for_dict():
    assert coerce_float({"x": 1}) is None


# ----------------------------------------------------------------------
# format_authors_etal
# ----------------------------------------------------------------------


def test_format_authors_single():
    assert format_authors_etal(["Solo Author"]) == "Solo Author"


def test_format_authors_multi_uses_et_al():
    assert format_authors_etal(["First", "Second", "Third"]) == "First et al."


def test_format_authors_two_authors_uses_et_al():
    """Two authors still get 'et al.' -- formal listing isn't worth the special case."""
    assert format_authors_etal(["First", "Second"]) == "First et al."


def test_format_authors_empty_list_is_none():
    assert format_authors_etal([]) is None


def test_format_authors_filters_falsy():
    assert format_authors_etal(["", None, "Real Author"]) == "Real Author"  # type: ignore[list-item]


def test_format_authors_filters_non_strings():
    assert format_authors_etal([{"name": "Bad"}, "Good"]) == "Good"  # type: ignore[list-item]


def test_format_authors_all_falsy_is_none():
    assert format_authors_etal(["", None, "  "]) is not None  # whitespace is "truthy" string


def test_format_authors_all_none_is_none():
    assert format_authors_etal([None, None]) is None  # type: ignore[list-item]


# ----------------------------------------------------------------------
# parse_date_utc
# ----------------------------------------------------------------------


def test_parse_date_utc_default_iso():
    d = parse_date_utc("2024-06-15")
    assert d == datetime(2024, 6, 15, tzinfo=timezone.utc)


def test_parse_date_utc_custom_format():
    d = parse_date_utc("2024/06/15", formats=("%Y/%m/%d",))
    assert d == datetime(2024, 6, 15, tzinfo=timezone.utc)


def test_parse_date_utc_multi_format_falls_through():
    """Tries each format in order; first match wins."""
    d = parse_date_utc("2024-06", formats=("%Y-%m-%d", "%Y-%m"))
    assert d == datetime(2024, 6, 1, tzinfo=timezone.utc)


def test_parse_date_utc_none_for_none():
    assert parse_date_utc(None) is None


def test_parse_date_utc_none_for_empty_string():
    assert parse_date_utc("") is None


def test_parse_date_utc_none_for_unparseable():
    assert parse_date_utc("not-a-date") is None


def test_parse_date_utc_none_for_non_string():
    assert parse_date_utc(12345) is None  # type: ignore[arg-type]


# ----------------------------------------------------------------------
# parse_iso_utc
# ----------------------------------------------------------------------


def test_parse_iso_utc_handles_z_suffix():
    d = parse_iso_utc("2024-06-15T12:30:00Z")
    assert d == datetime(2024, 6, 15, 12, 30, 0, tzinfo=timezone.utc)


def test_parse_iso_utc_handles_offset():
    d = parse_iso_utc("2024-06-15T12:30:00+00:00")
    assert d == datetime(2024, 6, 15, 12, 30, 0, tzinfo=timezone.utc)


def test_parse_iso_utc_tags_utc_when_naive():
    d = parse_iso_utc("2024-06-15")
    assert d == datetime(2024, 6, 15, tzinfo=timezone.utc)


def test_parse_iso_utc_none_for_none():
    assert parse_iso_utc(None) is None


def test_parse_iso_utc_none_for_unparseable():
    assert parse_iso_utc("not-a-date") is None


# ----------------------------------------------------------------------
# since_date / cutoff_datetime
# ----------------------------------------------------------------------


def test_since_date_default_iso_format():
    s = since_date(30)
    assert s is not None
    assert len(s) == 10
    assert s[4] == "-"
    assert s[7] == "-"


def test_since_date_slash_format():
    s = since_date(30, fmt="%Y/%m/%d")
    assert s is not None
    assert s[4] == "/"
    assert s[7] == "/"


def test_since_date_none_for_zero():
    assert since_date(0) is None


def test_since_date_none_for_negative():
    assert since_date(-5) is None


def test_since_date_is_actually_days_ago():
    """A 30-day window should produce a date roughly 30 days before now.

    `since_date` truncates the result to a date string (midnight UTC), so
    parsing it back and subtracting from now yields between 30 and 31 days
    depending on the current time of day.
    """
    s = since_date(30)
    parsed = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - parsed
    assert timedelta(days=30) <= delta < timedelta(days=31)


def test_cutoff_datetime_returns_datetime():
    c = cutoff_datetime(30)
    assert c is not None
    assert c.tzinfo == timezone.utc
    delta = datetime.now(timezone.utc) - c
    assert timedelta(days=29, hours=23) < delta < timedelta(days=30, hours=1)


def test_cutoff_datetime_none_for_zero():
    assert cutoff_datetime(0) is None


def test_cutoff_datetime_none_for_negative():
    assert cutoff_datetime(-1) is None


# ----------------------------------------------------------------------
# fetch_json / fetch_text
#
# These are tested against an invalid (RFC 6761 reserved) hostname so the
# DNS lookup fails locally without touching the public internet. Tests
# verify only the "returns default on failure" contract; success-path
# behavior is exercised by the live adapter smoke tests.
# ----------------------------------------------------------------------

INVALID_URL = "http://localhost.invalid./digest-test"  # RFC 6761 reserved -- DNS resolves NXDOMAIN


def test_fetch_json_returns_default_on_network_error():
    assert fetch_json(INVALID_URL, default=[], timeout=2.0) == []


def test_fetch_json_default_is_none_when_unspecified():
    assert fetch_json(INVALID_URL, timeout=2.0) is None


def test_fetch_json_preserves_default_shape():
    """A dict default lets callers immediately call .get() without an or-chain."""
    payload = fetch_json(INVALID_URL, default={"results": []}, timeout=2.0)
    assert payload == {"results": []}


def test_fetch_text_returns_empty_string_on_network_error():
    assert fetch_text(INVALID_URL, timeout=2.0) == ""


def test_fetch_text_returns_custom_default():
    assert fetch_text(INVALID_URL, default="<fallback/>", timeout=2.0) == "<fallback/>"
