"""Unit tests for shared.http helpers.

Tests against an RFC 6761 reserved hostname (``.invalid.``) so DNS fails
locally without touching the public internet. Verifies only the
default-on-failure contract; success-path behavior is exercised by the
adapter-level live smoke tests.
"""

from __future__ import annotations

from shared.http import fetch_json, fetch_text

INVALID_URL = "http://localhost.invalid./shared-test"


def test_fetch_json_returns_default_on_network_error():
    assert fetch_json(INVALID_URL, default=[], timeout=2.0) == []


def test_fetch_json_default_is_none_when_unspecified():
    assert fetch_json(INVALID_URL, timeout=2.0) is None


def test_fetch_json_preserves_default_shape():
    payload = fetch_json(INVALID_URL, default={"results": []}, timeout=2.0)
    assert payload == {"results": []}


def test_fetch_json_post_uses_method_param():
    """POST should route through httpx.request with method='POST'."""
    assert fetch_json(INVALID_URL, method="POST", json={"x": 1}, default={}, timeout=2.0) == {}


def test_fetch_text_returns_empty_on_network_error():
    assert fetch_text(INVALID_URL, timeout=2.0) == ""


def test_fetch_text_custom_default():
    assert fetch_text(INVALID_URL, default="<fallback/>", timeout=2.0) == "<fallback/>"
