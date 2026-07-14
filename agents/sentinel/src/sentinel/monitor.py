"""Transaction monitoring and alert evaluation."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone

from shared.chains import blockscout_hosts, fetch_blockscout_json
from shared.dates import parse_iso_utc

from sentinel.models import Alert, ContractWatch, Transaction
from sentinel.rules import ALL_RULES

logger = logging.getLogger(__name__)


def get_blockscout_url(chain_id: int) -> str:
    """Map a chain_id to its primary Blockscout instance URL."""
    return blockscout_hosts(chain_id)[0]


def _parse_transaction(raw: dict) -> Transaction:
    """Parse a Blockscout API v2 transaction response into a Transaction."""
    method_id = None
    raw_input = raw.get("raw_input") or raw.get("input")
    if raw_input and len(raw_input) >= 10:
        method_id = raw_input[:10]

    ts = parse_iso_utc(raw.get("timestamp") or raw.get("block_timestamp")) or datetime.now(
        timezone.utc
    )

    to_addr = raw.get("to")
    if isinstance(to_addr, dict):
        to_addr = to_addr.get("hash")
    from_addr = raw.get("from")
    if isinstance(from_addr, dict):
        from_addr = from_addr.get("hash")

    return Transaction(
        hash=raw.get("hash", ""),
        from_address=from_addr or "",
        to_address=to_addr,
        value_wei=int(raw.get("value", "0")),
        method_id=method_id,
        block_number=int(raw.get("block_number", 0)),
        timestamp=ts,
    )


def fetch_transactions(
    address: str,
    chain_id: int = 1,
    since_block: int | None = None,
) -> list[Transaction]:
    """Fetch recent transactions for an address from Blockscout API v2."""
    params: dict[str, str] = {}
    if since_block is not None:
        params["start_block"] = str(since_block)

    data = fetch_blockscout_json(
        chain_id,
        f"/api/v2/addresses/{address}/transactions",
        params=params,
        default={},
    )
    items = data.get("items", []) or []
    txs = [_parse_transaction(item) for item in items]

    if since_block is not None:
        txs = [tx for tx in txs if tx.block_number >= since_block]

    return txs


def evaluate_alerts(
    txs: list[Transaction],
    watch: ContractWatch,
    rules: list[Callable] | None = None,
) -> list[Alert]:
    """Run all rules against all transactions, collecting triggered alerts."""
    if rules is None:
        rules = ALL_RULES

    alerts: list[Alert] = []
    for tx in txs:
        for rule in rules:
            alert = rule(tx, watch)
            if alert is not None:
                alerts.append(alert)
    return alerts
