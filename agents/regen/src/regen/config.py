"""Runtime configuration for the Regen client, resolved from the environment.

Regen OSS v1.0.0 has no API-token auth: ``RequireAuth`` accepts a local session
cookie (``oi_session``) or SAML, and falls through to open mode when neither is
configured. We therefore support three connection modes, in priority order:

1. ``REGEN_SESSION_COOKIE`` -- sent as the ``oi_session`` cookie.
2. ``REGEN_API_TOKEN``      -- sent as ``Authorization: Bearer`` (forward-compatible
   with a future/Pro token; harmless against an open-mode instance).
3. neither                  -- open mode (typical for a Tailscale-internal deploy).
"""

from __future__ import annotations

import os

from pydantic import BaseModel

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env_bool(name: str, *, default: bool = False) -> bool:
    """Read a boolean-ish environment variable (1/true/yes/on -> True)."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUTHY


class RegenConfig(BaseModel):
    """Connection + capability settings for a Regen instance."""

    base_url: str = ""
    session_cookie: str | None = None
    api_token: str | None = None
    enable_write: bool = False
    timeout: float = 30.0

    @classmethod
    def from_env(
        cls,
        *,
        base_url: str | None = None,
        enable_write: bool | None = None,
    ) -> RegenConfig:
        """Build a config from environment variables, with optional CLI overrides.

        ``base_url`` and ``enable_write`` overrides win over the environment so
        CLI flags can take precedence; secrets are only read from the environment.
        """
        resolved_url = base_url if base_url is not None else os.environ.get("REGEN_BASE_URL", "")
        resolved_write = (
            enable_write if enable_write is not None else _env_bool("REGEN_ENABLE_WRITE")
        )
        return cls(
            base_url=resolved_url.rstrip("/"),
            session_cookie=os.environ.get("REGEN_SESSION_COOKIE") or None,
            api_token=os.environ.get("REGEN_API_TOKEN") or None,
            enable_write=resolved_write,
        )
