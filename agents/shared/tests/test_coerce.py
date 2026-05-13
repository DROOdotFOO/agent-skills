"""Unit tests for shared.coerce helpers."""

from __future__ import annotations

from shared.coerce import coerce_float, coerce_int, format_authors_etal


# ----------------------------------------------------------------------
# coerce_int
# ----------------------------------------------------------------------


def test_coerce_int_passes_through_int():
    assert coerce_int(42) == 42


def test_coerce_int_parses_string():
    assert coerce_int("100") == 100


def test_coerce_int_zero_for_none():
    assert coerce_int(None) == 0


def test_coerce_int_zero_for_unparseable():
    assert coerce_int("not-a-number") == 0


def test_coerce_int_zero_for_dict():
    assert coerce_int({"foo": 1}) == 0


def test_coerce_int_truncates_float():
    assert coerce_int(3.9) == 3


# ----------------------------------------------------------------------
# coerce_float
# ----------------------------------------------------------------------


def test_coerce_float_passes_through():
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


def test_format_authors_two_authors_use_et_al():
    assert format_authors_etal(["First", "Second"]) == "First et al."


def test_format_authors_empty_list_is_none():
    assert format_authors_etal([]) is None


def test_format_authors_filters_falsy():
    assert format_authors_etal(["", None, "Real"]) == "Real"  # type: ignore[list-item]


def test_format_authors_filters_non_strings():
    assert format_authors_etal([{"name": "Bad"}, "Good"]) == "Good"  # type: ignore[list-item]


def test_format_authors_all_none_is_none():
    assert format_authors_etal([None, None]) is None  # type: ignore[list-item]
