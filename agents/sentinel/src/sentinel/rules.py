"""Alert rule definitions for contract monitoring.

Each rule is a function that evaluates a single transaction against a
ContractWatch config and returns an Alert if the condition is met, or None.
"""

from __future__ import annotations

from collections.abc import Callable

from sentinel.models import Alert, AlertSeverity, ContractWatch, Transaction

WEI_PER_ETH = 10**18

# Well-known method selectors for ownership changes
OWNERSHIP_METHODS: dict[str, str] = {
    "0xf2fde38b": "transferOwnership(address)",
    "0x715018a6": "renounceOwnership()",
}

# selfdestruct is an opcode (0xff), but proxy patterns sometimes expose it
# via a method. We check for known wrapper selectors.
SELFDESTRUCT_METHODS: dict[str, str] = {
    "0x9cb8a26a": "destroy()",
    "0x00f55d9d": "destroyAndSend(address)",
    "0x43d726d6": "close()",
}


def check_large_transfer(tx: Transaction, watch: ContractWatch) -> Alert | None:
    """Alert when a transaction value exceeds a threshold (default 10 ETH)."""
    threshold_eth = watch.alert_thresholds.get("large_transfer_eth", 10.0)
    value_eth = tx.value_wei / WEI_PER_ETH
    if value_eth >= threshold_eth:
        return Alert(
            contract=watch,
            severity=AlertSeverity.HIGH,
            rule_name="large_transfer",
            message=f"Transfer of {value_eth:.4f} ETH exceeds threshold of {threshold_eth} ETH",
            tx_hash=tx.hash,
            value=value_eth,
        )
    return None


def check_ownership_change(tx: Transaction, watch: ContractWatch) -> Alert | None:
    """Alert when a known ownership-transfer method is called."""
    if tx.method_id and tx.method_id in OWNERSHIP_METHODS:
        method_name = OWNERSHIP_METHODS[tx.method_id]
        return Alert(
            contract=watch,
            severity=AlertSeverity.CRITICAL,
            rule_name="ownership_change",
            message=f"Ownership function called: {method_name}",
            tx_hash=tx.hash,
        )
    return None


def check_unusual_method(
    tx: Transaction,
    watch: ContractWatch,
    known_methods: set[str] | None = None,
) -> Alert | None:
    """Alert when a method_id is not in the known set for this contract."""
    if known_methods is None:
        return None
    if tx.method_id and tx.method_id not in known_methods:
        return Alert(
            contract=watch,
            severity=AlertSeverity.MEDIUM,
            rule_name="unusual_method",
            message=f"Unknown method called: {tx.method_id}",
            tx_hash=tx.hash,
        )
    return None


def check_contract_selfdestruct(tx: Transaction, watch: ContractWatch) -> Alert | None:
    """Alert when a selfdestruct-related method is called."""
    if tx.method_id and tx.method_id in SELFDESTRUCT_METHODS:
        method_name = SELFDESTRUCT_METHODS[tx.method_id]
        return Alert(
            contract=watch,
            severity=AlertSeverity.CRITICAL,
            rule_name="contract_selfdestruct",
            message=f"Selfdestruct pattern detected: {method_name}",
            tx_hash=tx.hash,
        )
    return None


RuleFunc = Callable[[Transaction, ContractWatch], Alert | None]

ALL_RULES: list[RuleFunc] = [
    check_large_transfer,
    check_ownership_change,
    check_contract_selfdestruct,
]
