"""Unit tests for Blockscout adapter helpers."""

from __future__ import annotations

from datetime import datetime

from digest.adapters.blockscout import BlockscoutAdapter, _addr, _parse_timestamp


def test_adapter_name():
    assert BlockscoutAdapter().name == "blockscout"


def test_parse_timestamp_iso():
    ts = _parse_timestamp("2024-06-01T12:00:00.000000Z")
    assert ts.year == 2024
    assert ts.month == 6
    assert ts.tzinfo is not None


def test_parse_timestamp_empty_returns_now():
    ts = _parse_timestamp("")
    assert ts.year >= 2024


def test_parse_timestamp_invalid_returns_now():
    ts = _parse_timestamp("not-a-date")
    assert isinstance(ts, datetime)


def test_addr_from_string():
    assert _addr("0xabc") == "0xabc"


def test_addr_from_dict():
    assert _addr({"hash": "0xdef"}) == "0xdef"


def test_addr_from_none():
    assert _addr(None) == ""


def test_addr_from_empty_dict():
    assert _addr({}) == ""
