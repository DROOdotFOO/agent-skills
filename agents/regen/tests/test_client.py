"""Tests for the Regen client's pure URL/auth/config builders (no network)."""

from __future__ import annotations

import pytest

from regen.client import RegenClient, build_auth_kwargs, build_url
from regen.config import RegenConfig

# --- build_url ---


def test_build_url_joins():
    assert build_url("http://host:3000", "/api/v1/incidents") == "http://host:3000/api/v1/incidents"


def test_build_url_empty_raises():
    with pytest.raises(ValueError, match="REGEN_BASE_URL"):
        build_url("", "/api/v1/incidents")


# --- build_auth_kwargs ---


def test_auth_cookie_mode():
    cfg = RegenConfig(base_url="http://h", session_cookie="sess-123")
    assert build_auth_kwargs(cfg) == {"cookies": {"oi_session": "sess-123"}}


def test_auth_bearer_mode():
    cfg = RegenConfig(base_url="http://h", api_token="tok-abc")
    assert build_auth_kwargs(cfg) == {"headers": {"Authorization": "Bearer tok-abc"}}


def test_auth_cookie_wins_over_token():
    cfg = RegenConfig(base_url="http://h", session_cookie="s", api_token="t")
    assert build_auth_kwargs(cfg) == {"cookies": {"oi_session": "s"}}


def test_auth_open_mode():
    cfg = RegenConfig(base_url="http://h")
    assert build_auth_kwargs(cfg) == {}


# --- RegenConfig.from_env ---


def test_from_env_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("REGEN_BASE_URL", "http://mini-axol:3000/")
    monkeypatch.delenv("REGEN_ENABLE_WRITE", raising=False)
    cfg = RegenConfig.from_env()
    assert cfg.base_url == "http://mini-axol:3000"
    assert cfg.enable_write is False


def test_from_env_reads_secrets_and_write(monkeypatch):
    monkeypatch.setenv("REGEN_BASE_URL", "http://h")
    monkeypatch.setenv("REGEN_SESSION_COOKIE", "sess")
    monkeypatch.setenv("REGEN_API_TOKEN", "tok")
    monkeypatch.setenv("REGEN_ENABLE_WRITE", "1")
    cfg = RegenConfig.from_env()
    assert cfg.session_cookie == "sess"
    assert cfg.api_token == "tok"
    assert cfg.enable_write is True


def test_from_env_base_url_override_wins(monkeypatch):
    monkeypatch.setenv("REGEN_BASE_URL", "http://env-host")
    cfg = RegenConfig.from_env(base_url="http://cli-host")
    assert cfg.base_url == "http://cli-host"


def test_from_env_enable_write_override_wins(monkeypatch):
    monkeypatch.setenv("REGEN_ENABLE_WRITE", "1")
    cfg = RegenConfig.from_env(enable_write=False)
    assert cfg.enable_write is False


def test_from_env_write_falsey_values(monkeypatch):
    monkeypatch.delenv("REGEN_BASE_URL", raising=False)
    monkeypatch.setenv("REGEN_ENABLE_WRITE", "no")
    assert RegenConfig.from_env().enable_write is False


# --- RegenClient._request_kwargs ---


def test_request_kwargs_merges_auth_timeout_extra():
    client = RegenClient(RegenConfig(base_url="http://h", session_cookie="s", timeout=12.0))
    kwargs = client._request_kwargs(params={"status": "triggered"})
    assert kwargs["cookies"] == {"oi_session": "s"}
    assert kwargs["timeout"] == 12.0
    assert kwargs["params"] == {"status": "triggered"}
