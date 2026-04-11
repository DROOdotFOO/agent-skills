"""Tests for sentinel alert rules.

All tests use synthetic Transaction objects. No network calls, no mocks.
"""

from datetime import datetime, timezone

from sentinel.models import AlertSeverity, ContractWatch, Transaction
from sentinel.monitor import evaluate_alerts
from sentinel.rules import (
    WEI_PER_ETH,
    check_contract_selfdestruct,
    check_large_transfer,
    check_ownership_change,
    check_unusual_method,
)


def _tx(**overrides) -> Transaction:
    defaults = {
        "hash": "0xaaa",
        "from_address": "0x1111111111111111111111111111111111111111",
        "to_address": "0x2222222222222222222222222222222222222222",
        "value_wei": 0,
        "method_id": None,
        "block_number": 500,
        "timestamp": datetime(2025, 6, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return Transaction(**defaults)


def _watch(**overrides) -> ContractWatch:
    defaults = {
        "address": "0x2222222222222222222222222222222222222222",
        "chain_id": 1,
        "name": "TestContract",
    }
    defaults.update(overrides)
    return ContractWatch(**defaults)


class TestLargeTransfer:
    def test_below_threshold_returns_none(self):
        tx = _tx(value_wei=5 * WEI_PER_ETH)
        assert check_large_transfer(tx, _watch()) is None

    def test_at_threshold_triggers(self):
        tx = _tx(value_wei=10 * WEI_PER_ETH)
        alert = check_large_transfer(tx, _watch())
        assert alert is not None
        assert alert.severity == AlertSeverity.HIGH
        assert alert.rule_name == "large_transfer"
        assert alert.value == 10.0

    def test_above_threshold_triggers(self):
        tx = _tx(value_wei=50 * WEI_PER_ETH)
        alert = check_large_transfer(tx, _watch())
        assert alert is not None
        assert alert.value == 50.0

    def test_custom_threshold(self):
        watch = _watch(alert_thresholds={"large_transfer_eth": 1.0})
        tx = _tx(value_wei=2 * WEI_PER_ETH)
        alert = check_large_transfer(tx, watch)
        assert alert is not None

    def test_custom_threshold_below(self):
        watch = _watch(alert_thresholds={"large_transfer_eth": 100.0})
        tx = _tx(value_wei=50 * WEI_PER_ETH)
        assert check_large_transfer(tx, watch) is None

    def test_zero_value_returns_none(self):
        tx = _tx(value_wei=0)
        assert check_large_transfer(tx, _watch()) is None


class TestOwnershipChange:
    def test_transfer_ownership_triggers(self):
        tx = _tx(method_id="0xf2fde38b")
        alert = check_ownership_change(tx, _watch())
        assert alert is not None
        assert alert.severity == AlertSeverity.CRITICAL
        assert "transferOwnership" in alert.message

    def test_renounce_ownership_triggers(self):
        tx = _tx(method_id="0x715018a6")
        alert = check_ownership_change(tx, _watch())
        assert alert is not None
        assert "renounceOwnership" in alert.message

    def test_normal_method_returns_none(self):
        tx = _tx(method_id="0xa9059cbb")
        assert check_ownership_change(tx, _watch()) is None

    def test_no_method_returns_none(self):
        tx = _tx(method_id=None)
        assert check_ownership_change(tx, _watch()) is None


class TestUnusualMethod:
    def test_unknown_method_triggers(self):
        known = {"0xa9059cbb", "0x23b872dd"}
        tx = _tx(method_id="0xdeadbeef")
        alert = check_unusual_method(tx, _watch(), known_methods=known)
        assert alert is not None
        assert alert.severity == AlertSeverity.MEDIUM
        assert "0xdeadbeef" in alert.message

    def test_known_method_returns_none(self):
        known = {"0xa9059cbb"}
        tx = _tx(method_id="0xa9059cbb")
        assert check_unusual_method(tx, _watch(), known_methods=known) is None

    def test_no_known_methods_returns_none(self):
        tx = _tx(method_id="0xdeadbeef")
        assert check_unusual_method(tx, _watch(), known_methods=None) is None

    def test_no_method_id_returns_none(self):
        known = {"0xa9059cbb"}
        tx = _tx(method_id=None)
        assert check_unusual_method(tx, _watch(), known_methods=known) is None


class TestContractSelfdestruct:
    def test_destroy_triggers(self):
        tx = _tx(method_id="0x9cb8a26a")
        alert = check_contract_selfdestruct(tx, _watch())
        assert alert is not None
        assert alert.severity == AlertSeverity.CRITICAL
        assert "destroy()" in alert.message

    def test_destroy_and_send_triggers(self):
        tx = _tx(method_id="0x00f55d9d")
        alert = check_contract_selfdestruct(tx, _watch())
        assert alert is not None

    def test_close_triggers(self):
        tx = _tx(method_id="0x43d726d6")
        alert = check_contract_selfdestruct(tx, _watch())
        assert alert is not None
        assert "close()" in alert.message

    def test_normal_method_returns_none(self):
        tx = _tx(method_id="0xa9059cbb")
        assert check_contract_selfdestruct(tx, _watch()) is None


class TestEvaluateAlerts:
    def test_multiple_rules_fire(self):
        # Large transfer + ownership change in same tx
        tx = _tx(value_wei=20 * WEI_PER_ETH, method_id="0xf2fde38b")
        alerts = evaluate_alerts([tx], _watch())
        rule_names = {a.rule_name for a in alerts}
        assert "large_transfer" in rule_names
        assert "ownership_change" in rule_names

    def test_no_alerts_for_benign_tx(self):
        tx = _tx(value_wei=1 * WEI_PER_ETH, method_id="0xa9059cbb")
        alerts = evaluate_alerts([tx], _watch())
        assert alerts == []

    def test_multiple_transactions(self):
        txs = [
            _tx(hash="0x1", value_wei=15 * WEI_PER_ETH),
            _tx(hash="0x2", value_wei=1 * WEI_PER_ETH),
            _tx(hash="0x3", method_id="0x715018a6"),
        ]
        alerts = evaluate_alerts(txs, _watch())
        assert len(alerts) == 2
        hashes = {a.tx_hash for a in alerts}
        assert "0x1" in hashes
        assert "0x3" in hashes

    def test_empty_transactions_returns_empty(self):
        assert evaluate_alerts([], _watch()) == []

    def test_custom_rules_list(self):
        tx = _tx(value_wei=20 * WEI_PER_ETH, method_id="0xf2fde38b")
        # Only run ownership check
        alerts = evaluate_alerts([tx], _watch(), rules=[check_ownership_change])
        assert len(alerts) == 1
        assert alerts[0].rule_name == "ownership_change"
