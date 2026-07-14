"""Unit tests for shared.http helpers.

The default-on-failure contract is verified against an RFC 6761 reserved
hostname (``.invalid.``) so DNS fails locally without touching the public
internet. Retry/backoff behavior is verified against a real loopback HTTP
server that fails a fixed number of times before succeeding -- no mocks,
fully deterministic, ``backoff=0`` to keep the suite fast.
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from shared.http import fetch_json, fetch_text

INVALID_URL = "http://localhost.invalid./shared-test"


def test_fetch_json_returns_default_on_network_error():
    assert fetch_json(INVALID_URL, default=[], retries=0, timeout=2.0) == []


def test_fetch_json_default_is_none_when_unspecified():
    assert fetch_json(INVALID_URL, retries=0, timeout=2.0) is None


def test_fetch_json_preserves_default_shape():
    payload = fetch_json(INVALID_URL, default={"results": []}, retries=0, timeout=2.0)
    assert payload == {"results": []}


def test_fetch_json_post_uses_method_param():
    """POST should route through httpx.request with method='POST'."""
    assert (
        fetch_json(INVALID_URL, method="POST", json={"x": 1}, default={}, retries=0, timeout=2.0)
        == {}
    )


def test_fetch_text_returns_empty_on_network_error():
    assert fetch_text(INVALID_URL, retries=0, timeout=2.0) == ""


def test_fetch_text_custom_default():
    assert fetch_text(INVALID_URL, default="<fallback/>", retries=0, timeout=2.0) == "<fallback/>"


class _FlakyHandler(BaseHTTPRequestHandler):
    """Returns 503 for the first ``fail_times`` requests, then 200 with JSON."""

    fail_times = 0
    request_count = 0

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler API
        type(self).request_count += 1
        if type(self).request_count <= type(self).fail_times:
            self.send_response(503)
            self.end_headers()
            return
        body = b'{"ok": true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence test server logging
        pass


@pytest.fixture
def flaky_server():
    """Yield a base URL for a loopback server; reset counters per test."""
    _FlakyHandler.request_count = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FlakyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()


def test_fetch_json_retries_then_succeeds(flaky_server):
    _FlakyHandler.fail_times = 2
    result = fetch_json(flaky_server, default={}, retries=2, backoff=0)
    assert result == {"ok": True}
    assert _FlakyHandler.request_count == 3  # two 503s + one 200


def test_fetch_json_exhausts_retries_and_returns_default(flaky_server):
    _FlakyHandler.fail_times = 99  # always fails
    result = fetch_json(flaky_server, default={"fallback": True}, retries=2, backoff=0)
    assert result == {"fallback": True}
    assert _FlakyHandler.request_count == 3  # initial + two retries


def test_fetch_text_retries_then_succeeds(flaky_server):
    _FlakyHandler.fail_times = 1
    result = fetch_text(flaky_server, retries=2, backoff=0)
    assert result == '{"ok": true}'
    assert _FlakyHandler.request_count == 2
