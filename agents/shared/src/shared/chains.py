"""Blockscout instance endpoints per chain, with failover support.

Single source of truth for the chain_id -> Blockscout host mapping shared by
the sentinel and digest agents (previously duplicated and drifting).

Each chain maps to an *ordered tuple* of Blockscout API v2 hosts: the primary
first, optional mirrors after. :func:`fetch_blockscout_json` tries them in
order until one succeeds, on top of the per-request retry/backoff in
:mod:`shared.http`.

Note: these are Blockscout REST API v2 hosts. Public JSON-RPC providers
(llamarpc, publicnode, drpc, ankr, ...) speak ``eth_*`` JSON-RPC, NOT the
Blockscout REST API, so they are not interchangeable fallbacks here. Add a
mirror only if it serves the same ``/api/v2`` surface. To add one, append it
to the chain's tuple below -- no other code change is needed.
"""

from __future__ import annotations

from typing import Any

from shared.http import fetch_json

BLOCKSCOUT_URLS: dict[int, tuple[str, ...]] = {
    1: ("https://eth.blockscout.com",),
    137: ("https://polygon.blockscout.com",),
    10: ("https://optimism.blockscout.com",),
    42161: ("https://arbitrum.blockscout.com",),
    8453: ("https://base.blockscout.com",),
    100: ("https://gnosis.blockscout.com",),
    324: ("https://zksync.blockscout.com",),
    534352: ("https://scroll.blockscout.com",),
    42220: ("https://celo.blockscout.com",),
    34443: ("https://explorer.mode.network",),
    245022934: ("https://neon.blockscout.com",),
}


def blockscout_hosts(chain_id: int) -> tuple[str, ...]:
    """Return the ordered Blockscout hosts for ``chain_id`` (primary first)."""
    hosts = BLOCKSCOUT_URLS.get(chain_id)
    if not hosts:
        raise ValueError(f"No Blockscout instance configured for chain_id={chain_id}")
    return hosts


def fetch_blockscout_json(
    chain_id: int,
    path: str,
    *,
    default: Any = None,
    **httpx_kwargs: Any,
) -> Any:
    """Fetch ``path`` from ``chain_id``'s Blockscout host(s), failing over on error.

    ``path`` is the API path beginning with ``/`` (e.g.
    ``/api/v2/addresses/0x.../transactions``). Each host is tried in order via
    :func:`shared.http.fetch_json` (which already retries transient errors);
    the first non-failing response is returned. Returns ``default`` only if
    every host fails.
    """
    hosts = blockscout_hosts(chain_id)
    miss = object()
    for host in hosts:
        result = fetch_json(f"{host}{path}", default=miss, **httpx_kwargs)
        if result is not miss:
            return result
    return default
