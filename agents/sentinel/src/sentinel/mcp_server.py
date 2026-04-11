"""FastMCP server exposing sentinel tools for Claude Code integration."""

from __future__ import annotations

import json
from pathlib import Path

from fastmcp import FastMCP

from sentinel.models import ContractWatch
from sentinel.monitor import evaluate_alerts, fetch_transactions
from sentinel.rules import ALL_RULES


def create_server() -> FastMCP:
    """Create a FastMCP server with sentinel tools."""
    mcp = FastMCP(
        "sentinel",
        instructions=(
            "On-chain contract monitor. Use sentinel_check to scan a contract address for "
            "anomalous transactions (large transfers, ownership changes, unusual methods, "
            "selfdestruct). Supports 8 chains via Blockscout API v2."
        ),
    )

    @mcp.tool()
    def sentinel_check(
        address: str,
        chain_id: int = 1,
        since_block: int | None = None,
    ) -> str:
        """Check a contract address for anomalous transactions.

        Runs 4 alert rules: large transfers, ownership changes, unusual methods, selfdestruct.

        Args:
            address: Contract address to check (0x...)
            chain_id: Chain ID (1=ETH, 137=Polygon, 8453=Base, 42161=Arb, 10=OP, 324=zkSync)
            since_block: Only check transactions from this block forward (optional)
        """
        watch = ContractWatch(address=address, chain_id=chain_id, name=address[:10])

        try:
            txs = fetch_transactions(address, chain_id=chain_id, since_block=since_block)
        except Exception as exc:
            return f"Error fetching transactions: {exc}"

        alerts = evaluate_alerts(txs, watch, ALL_RULES)

        lines = [f"Checked {address} on chain {chain_id}: {len(txs)} transactions"]

        if not alerts:
            lines.append("No alerts triggered.")
            return "\n".join(lines)

        lines.append(f"{len(alerts)} alert(s):\n")
        for alert in alerts:
            severity = alert.severity.value.upper()
            lines.append(f"[{severity}] {alert.rule_name}: {alert.message}")
            if alert.tx_hash:
                lines.append(f"  TX: {alert.tx_hash}")

        return "\n".join(lines)

    @mcp.tool()
    def sentinel_alerts(
        log_file: str = "alerts.jsonl",
        limit: int = 20,
    ) -> str:
        """Show recent alerts from the local alerts.jsonl log.

        Args:
            log_file: Path to the alerts JSONL log file (default: alerts.jsonl)
            limit: Max alerts to return (default 20)
        """
        path = Path(log_file)
        if not path.exists():
            return "No alerts log found."

        lines_raw = path.read_text().strip().splitlines()
        recent = lines_raw[-limit:] if len(lines_raw) > limit else lines_raw

        output_lines = [f"Recent alerts ({len(recent)} of {len(lines_raw)} total):\n"]
        for line in reversed(recent):
            data = json.loads(line)
            severity = data.get("severity", "").upper()
            rule = data.get("rule_name", "")
            contract = data.get("contract", {}).get("name", "")
            message = data.get("message", "")
            tx = (data.get("tx_hash") or "")[:16]
            output_lines.append(f"[{severity}] {rule} ({contract}): {message} tx={tx}...")

        return "\n".join(output_lines)

    return mcp
