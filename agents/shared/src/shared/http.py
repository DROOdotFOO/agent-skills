"""HTTP fetch helpers shared across agents.

Wraps ``httpx`` with default-on-error semantics so callers can keep their
fetch sites short and treat the result as the expected shape (dict, list,
str) without an ``or`` chain.
"""

from __future__ import annotations

from typing import Any

import httpx


def fetch_json(
    url: str,
    *,
    method: str = "GET",
    default: Any = None,
    **httpx_kwargs: Any,
) -> Any:
    """Issue ``method`` to ``url`` and return parsed JSON, or ``default`` on failure.

    Catches both HTTP errors (timeout, connection, non-2xx via
    ``raise_for_status``) and JSON parse errors. Callers should pass a
    ``default`` matching the expected shape -- usually ``[]`` or ``{}`` so
    they can keep treating the result as a list/dict without an explicit
    ``or`` chain.

    Accepts any keyword args ``httpx.request`` accepts (``params``,
    ``headers``, ``json``, ``follow_redirects``, etc.). Sets a 30s timeout
    by default. ``method`` defaults to ``"GET"``; use ``"POST"`` for
    GraphQL-style endpoints.
    """
    httpx_kwargs.setdefault("timeout", 30.0)
    try:
        response = httpx.request(method, url, **httpx_kwargs)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError):
        return default


def fetch_text(url: str, *, default: str = "", **httpx_kwargs: Any) -> str:
    """GET ``url`` and return the response body as text, or ``default`` on failure.

    Use for XML / RSS / plaintext APIs. Catches HTTP errors but not parse
    errors (the body is returned untransformed). Default 30s timeout.
    """
    httpx_kwargs.setdefault("timeout", 30.0)
    try:
        response = httpx.get(url, **httpx_kwargs)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError:
        return default
