"""Unit tests for shared.chains Blockscout host mapping and failover.

Failover is verified against real loopback servers (no mocks): a failing
server followed by a healthy one, asserting the healthy response is returned.
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from shared.chains import BLOCKSCOUT_URLS, blockscout_hosts, fetch_blockscout_json


def test_known_chains_return_ordered_hosts():
    assert blockscout_hosts(1)[0] == "https://eth.blockscout.com"
    assert "base" in blockscout_hosts(8453)[0]
    assert "polygon" in blockscout_hosts(137)[0]


def test_all_hosts_are_nonempty_tuples():
    for chain_id, hosts in BLOCKSCOUT_URLS.items():
        assert isinstance(hosts, tuple) and hosts, chain_id
        assert all(h.startswith("https://") for h in hosts), chain_id


def test_unknown_chain_raises():
    with pytest.raises(ValueError, match="chain_id=999999"):
        blockscout_hosts(999999)


class _StatusHandler(BaseHTTPRequestHandler):
    status = 200
    body = b'{"ok": true}'

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler API
        self.send_response(type(self).status)
        if type(self).status == 200:
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(type(self).body)))
            self.end_headers()
            self.wfile.write(type(self).body)
        else:
            self.end_headers()

    def log_message(self, *args):
        pass


def _serve(status: int):
    handler = type(f"H{status}", (_StatusHandler,), {"status": status})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}"


def test_fetch_blockscout_json_fails_over_to_healthy_host(monkeypatch):
    bad_server, bad_url = _serve(503)
    good_server, good_url = _serve(200)
    try:
        monkeypatch.setitem(BLOCKSCOUT_URLS, 999, (bad_url, good_url))
        result = fetch_blockscout_json(999, "/api/v2/anything", default={}, retries=0, backoff=0)
        assert result == {"ok": True}
    finally:
        for s in (bad_server, good_server):
            s.shutdown()
            s.server_close()


def test_fetch_blockscout_json_returns_default_when_all_hosts_fail(monkeypatch):
    bad_server, bad_url = _serve(503)
    try:
        monkeypatch.setitem(BLOCKSCOUT_URLS, 999, (bad_url,))
        result = fetch_blockscout_json(
            999, "/api/v2/anything", default={"fallback": True}, retries=0, backoff=0
        )
        assert result == {"fallback": True}
    finally:
        bad_server.shutdown()
        bad_server.server_close()
