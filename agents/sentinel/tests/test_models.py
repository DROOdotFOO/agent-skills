"""Tests for sentinel data models."""

from datetime import datetime, timezone

from sentinel.models import Alert, AlertSeverity, ContractWatch, Transaction, WatchConfig


def _make_tx(**overrides) -> Transaction:
    defaults = {
        "hash": "0xabc123",
        "from_address": "0x1111111111111111111111111111111111111111",
        "to_address": "0x2222222222222222222222222222222222222222",
        "value_wei": 0,
        "method_id": None,
        "block_number": 100,
        "timestamp": datetime(2025, 1, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return Transaction(**defaults)


def _make_watch(**overrides) -> ContractWatch:
    defaults = {
        "address": "0x2222222222222222222222222222222222222222",
        "chain_id": 1,
        "name": "TestContract",
    }
    defaults.update(overrides)
    return ContractWatch(**defaults)


class TestAlertSeverity:
    def test_ordering_values(self):
        assert AlertSeverity.CRITICAL.value == "critical"
        assert AlertSeverity.HIGH.value == "high"
        assert AlertSeverity.MEDIUM.value == "medium"
        assert AlertSeverity.LOW.value == "low"
        assert AlertSeverity.INFO.value == "info"

    def test_all_severities_are_strings(self):
        for severity in AlertSeverity:
            assert isinstance(severity.value, str)


class TestContractWatch:
    def test_defaults(self):
        watch = ContractWatch(address="0xdead")
        assert watch.chain_id == 1
        assert watch.name == ""
        assert watch.alert_thresholds == {}

    def test_custom_thresholds(self):
        watch = _make_watch(alert_thresholds={"large_transfer_eth": 5.0})
        assert watch.alert_thresholds["large_transfer_eth"] == 5.0


class TestWatchConfig:
    def test_defaults(self):
        cfg = WatchConfig()
        assert cfg.contracts == []
        assert cfg.poll_interval_seconds == 300
        assert cfg.alert_webhook is None

    def test_with_contracts(self):
        watch = _make_watch()
        cfg = WatchConfig(contracts=[watch], poll_interval_seconds=60)
        assert len(cfg.contracts) == 1
        assert cfg.poll_interval_seconds == 60


class TestTransaction:
    def test_basic_construction(self):
        tx = _make_tx(value_wei=10**18)
        assert tx.value_wei == 10**18
        assert tx.method_id is None

    def test_with_method_id(self):
        tx = _make_tx(method_id="0xf2fde38b")
        assert tx.method_id == "0xf2fde38b"

    def test_optional_to_address(self):
        tx = _make_tx(to_address=None)
        assert tx.to_address is None


class TestAlert:
    def test_alert_has_timestamp(self):
        watch = _make_watch()
        alert = Alert(
            contract=watch,
            severity=AlertSeverity.HIGH,
            rule_name="test_rule",
            message="test message",
        )
        assert alert.timestamp is not None
        assert alert.tx_hash is None
        assert alert.value is None

    def test_alert_with_tx_hash(self):
        watch = _make_watch()
        alert = Alert(
            contract=watch,
            severity=AlertSeverity.CRITICAL,
            rule_name="ownership_change",
            message="Ownership transferred",
            tx_hash="0xdeadbeef",
            value=100.5,
        )
        assert alert.tx_hash == "0xdeadbeef"
        assert alert.value == 100.5
