"""Tests for sentinel monitor parsing and alert evaluation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from sentinel.models import Alert, AlertSeverity, ContractWatch, Transaction
from sentinel.monitor import _parse_transaction, evaluate_alerts, get_blockscout_url


# --- get_blockscout_url ---


def test_ethereum_url():
    assert "eth.blockscout.com" in get_blockscout_url(1)


def test_base_url():
    assert "base" in get_blockscout_url(8453)


def test_neon_evm_url():
    assert get_blockscout_url(245022934) is not None


def test_unknown_chain_raises():
    with pytest.raises(ValueError, match="No Blockscout instance"):
        get_blockscout_url(999999)


# --- _parse_transaction ---


def test_parse_basic_transaction():
    raw = {
        "hash": "0xabc123",
        "from": "0xsender",
        "to": "0xreceiver",
        "value": "1000000000000000000",
        "block_number": 12345,
        "timestamp": "2024-06-01T12:00:00Z",
    }
    tx = _parse_transaction(raw)
    assert tx.hash == "0xabc123"
    assert tx.from_address == "0xsender"
    assert tx.to_address == "0xreceiver"
    assert tx.value_wei == 1_000_000_000_000_000_000
    assert tx.block_number == 12345
    assert tx.timestamp.year == 2024


def test_parse_dict_addresses():
    raw = {
        "hash": "0x1",
        "from": {"hash": "0xfrom_hash"},
        "to": {"hash": "0xto_hash"},
        "value": "0",
        "block_number": 1,
        "timestamp": "2024-01-01T00:00:00Z",
    }
    tx = _parse_transaction(raw)
    assert tx.from_address == "0xfrom_hash"
    assert tx.to_address == "0xto_hash"


def test_parse_method_id_from_raw_input():
    raw = {
        "hash": "0x1",
        "from": "0xa",
        "to": "0xb",
        "value": "0",
        "block_number": 1,
        "timestamp": "2024-01-01T00:00:00Z",
        "raw_input": "0xa9059cbb000000000000000000000000abcdef",
    }
    tx = _parse_transaction(raw)
    assert tx.method_id == "0xa9059cbb"


def test_parse_method_id_from_input_field():
    raw = {
        "hash": "0x1",
        "from": "0xa",
        "to": "0xb",
        "value": "0",
        "block_number": 1,
        "timestamp": "2024-01-01T00:00:00Z",
        "input": "0xf2fde38b000000000000000000000000abcdef",
    }
    tx = _parse_transaction(raw)
    assert tx.method_id == "0xf2fde38b"


def test_parse_no_method_id_for_plain_transfer():
    raw = {
        "hash": "0x1",
        "from": "0xa",
        "to": "0xb",
        "value": "0",
        "block_number": 1,
        "timestamp": "2024-01-01T00:00:00Z",
        "raw_input": "0x",
    }
    tx = _parse_transaction(raw)
    assert tx.method_id is None


def test_parse_missing_timestamp_defaults_to_now():
    raw = {
        "hash": "0x1",
        "from": "0xa",
        "to": "0xb",
        "value": "0",
        "block_number": 1,
    }
    tx = _parse_transaction(raw)
    assert tx.timestamp.year >= 2024


def test_parse_null_to_address():
    raw = {
        "hash": "0x1",
        "from": "0xa",
        "to": None,
        "value": "0",
        "block_number": 1,
        "timestamp": "2024-01-01T00:00:00Z",
    }
    tx = _parse_transaction(raw)
    assert tx.to_address is None


# --- evaluate_alerts ---


def test_evaluate_alerts_empty_txs():
    watch = ContractWatch(address="0x1", chain_id=1)
    alerts = evaluate_alerts([], watch)
    assert alerts == []


def test_evaluate_alerts_with_custom_rules():
    watch = ContractWatch(address="0x1", chain_id=1)
    tx = Transaction(
        hash="0x1",
        from_address="0xa",
        to_address="0xb",
        value_wei=0,
        block_number=1,
        timestamp=datetime.now(timezone.utc),
    )

    def always_alert(t: Transaction, w: ContractWatch) -> Alert | None:
        return Alert(
            contract=w,
            severity=AlertSeverity.INFO,
            rule_name="test_rule",
            message="test alert",
        )

    alerts = evaluate_alerts([tx], watch, rules=[always_alert])
    assert len(alerts) == 1
    assert alerts[0].rule_name == "test_rule"


def test_evaluate_alerts_rule_returning_none():
    watch = ContractWatch(address="0x1", chain_id=1)
    tx = Transaction(
        hash="0x1",
        from_address="0xa",
        to_address="0xb",
        value_wei=0,
        block_number=1,
        timestamp=datetime.now(timezone.utc),
    )

    def no_alert(t: Transaction, w: ContractWatch) -> Alert | None:
        return None

    alerts = evaluate_alerts([tx], watch, rules=[no_alert])
    assert alerts == []
