"""HTTP fetch helpers shared across agents.

Wraps ``httpx`` with default-on-error semantics so callers can keep their
fetch sites short and treat the result as the expected shape (dict, list,
str) without an ``or`` chain.

Transient failures (timeouts, connection errors, HTTP 429/5xx) are retried
with exponential backoff before falling back to ``default``. Every terminal
failure is logged -- the helpers never swallow an error silently.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Statuses worth retrying: rate limiting and transient server-side errors.
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


def _sleep_backoff(backoff: float, attempt: int) -> None:
    """Sleep for ``backoff * 2**attempt`` seconds (no-op when backoff <= 0)."""
    delay = backoff * (2**attempt)
    if delay > 0:
        time.sleep(delay)


def fetch_json(
    url: str,
    *,
    method: str = "GET",
    default: Any = None,
    retries: int = 2,
    backoff: float = 0.5,
    **httpx_kwargs: Any,
) -> Any:
    """Issue ``method`` to ``url`` and return parsed JSON, or ``default`` on failure.

    Retries transient failures (connection/timeout errors and HTTP
    ``429``/``5xx``) up to ``retries`` times with exponential backoff
    (``backoff * 2**attempt`` seconds). Non-retryable ``4xx`` responses and
    JSON parse errors fail immediately. Every terminal failure is logged at
    WARNING before ``default`` is returned.

    Callers should pass a ``default`` matching the expected shape -- usually
    ``[]`` or ``{}`` so they can keep treating the result as a list/dict
    without an explicit ``or`` chain.

    Accepts any keyword args ``httpx.request`` accepts (``params``,
    ``headers``, ``json``, ``follow_redirects``, etc.). Sets a 30s timeout
    by default. ``method`` defaults to ``"GET"``; use ``"POST"`` for
    GraphQL-style endpoints.
    """
    httpx_kwargs.setdefault("timeout", 30.0)
    for attempt in range(retries + 1):
        last = attempt == retries
        try:
            response = httpx.request(method, url, **httpx_kwargs)
            if response.status_code in RETRYABLE_STATUS and not last:
                logger.warning(
                    "fetch_json %s returned %s, retrying (%d/%d)",
                    url,
                    response.status_code,
                    attempt + 1,
                    retries,
                )
                _sleep_backoff(backoff, attempt)
                continue
            response.raise_for_status()
            return response.json()
        except httpx.TransportError as exc:  # timeout, connection, DNS, etc.
            if not last:
                logger.warning(
                    "fetch_json %s failed (%s), retrying (%d/%d)",
                    url,
                    exc,
                    attempt + 1,
                    retries,
                )
                _sleep_backoff(backoff, attempt)
                continue
            logger.warning("fetch_json %s failed after %d attempts: %s", url, retries + 1, exc)
            return default
        except (httpx.HTTPStatusError, ValueError) as exc:
            logger.warning("fetch_json %s failed: %s", url, exc)
            return default
    return default


def fetch_text(
    url: str,
    *,
    default: str = "",
    retries: int = 2,
    backoff: float = 0.5,
    **httpx_kwargs: Any,
) -> str:
    """GET ``url`` and return the response body as text, or ``default`` on failure.

    Use for XML / RSS / plaintext APIs. Retries transient failures like
    :func:`fetch_json`; parse errors do not apply since the body is returned
    untransformed. Logs terminal failures at WARNING. Default 30s timeout.
    """
    httpx_kwargs.setdefault("timeout", 30.0)
    for attempt in range(retries + 1):
        last = attempt == retries
        try:
            response = httpx.get(url, **httpx_kwargs)
            if response.status_code in RETRYABLE_STATUS and not last:
                logger.warning(
                    "fetch_text %s returned %s, retrying (%d/%d)",
                    url,
                    response.status_code,
                    attempt + 1,
                    retries,
                )
                _sleep_backoff(backoff, attempt)
                continue
            response.raise_for_status()
            return response.text
        except httpx.TransportError as exc:
            if not last:
                logger.warning(
                    "fetch_text %s failed (%s), retrying (%d/%d)",
                    url,
                    exc,
                    attempt + 1,
                    retries,
                )
                _sleep_backoff(backoff, attempt)
                continue
            logger.warning("fetch_text %s failed after %d attempts: %s", url, retries + 1, exc)
            return default
        except httpx.HTTPStatusError as exc:
            logger.warning("fetch_text %s failed: %s", url, exc)
            return default
    return default
