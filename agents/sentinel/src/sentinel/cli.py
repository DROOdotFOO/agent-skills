"""Typer CLI for sentinel contract monitoring."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from sentinel.models import ContractWatch, WatchConfig
from sentinel.monitor import evaluate_alerts, fetch_transactions
from sentinel.rules import ALL_RULES

app = typer.Typer(help="Sentinel: on-chain contract monitor for anomalous transactions.")
console = Console()

ALERTS_LOG = Path("alerts.jsonl")


def _load_config(config_path: Path) -> WatchConfig:
    """Load a sentinel.toml config file."""
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    text = config_path.read_text()
    data = tomllib.loads(text)

    contracts = []
    for entry in data.get("contracts", []):
        contracts.append(ContractWatch(**entry))

    return WatchConfig(
        contracts=contracts,
        poll_interval_seconds=data.get("poll_interval_seconds", 300),
        alert_webhook=data.get("alert_webhook"),
    )


def _append_alerts(alerts: list, log_path: Path) -> None:
    """Append alerts to a JSONL log file."""
    with log_path.open("a") as f:
        for alert in alerts:
            f.write(alert.model_dump_json() + "\n")


@app.command()
def check(
    address: str = typer.Option(..., "--address", "-a", help="Contract address to check"),
    chain: int = typer.Option(1, "--chain", "-c", help="Chain ID (default: 1 = Ethereum)"),
    since_block: int | None = typer.Option(None, "--since-block", "-s", help="Start block"),
    output: Path = typer.Option(ALERTS_LOG, "--output", "-o", help="Alerts log file"),
) -> None:
    """One-shot check of a contract address for anomalous transactions."""
    watch = ContractWatch(address=address, chain_id=chain, name=address[:10])
    console.print(f"Checking {address} on chain {chain}...")

    txs = fetch_transactions(address, chain_id=chain, since_block=since_block)
    console.print(f"Fetched {len(txs)} transactions.")

    alerts = evaluate_alerts(txs, watch, ALL_RULES)
    if alerts:
        _append_alerts(alerts, output)
        for alert in alerts:
            console.print(
                f"[bold red][{alert.severity.value.upper()}][/bold red] "
                f"{alert.rule_name}: {alert.message}"
            )
        console.print(f"\n{len(alerts)} alert(s) written to {output}")
    else:
        console.print("[green]No alerts.[/green]")


@app.command()
def watch(
    config: Path = typer.Option(Path("sentinel.toml"), "--config", "-f", help="Config file path"),
    output: Path = typer.Option(ALERTS_LOG, "--output", "-o", help="Alerts log file"),
) -> None:
    """Continuous monitoring loop reading from sentinel.toml."""
    import time

    if not config.exists():
        console.print(f"[red]Config not found: {config}[/red]")
        raise typer.Exit(1)

    cfg = _load_config(config)
    console.print(
        f"Watching {len(cfg.contracts)} contract(s), polling every {cfg.poll_interval_seconds}s"
    )

    while True:
        for contract in cfg.contracts:
            label = contract.name or contract.address[:10]
            try:
                txs = fetch_transactions(contract.address, chain_id=contract.chain_id)
                alerts = evaluate_alerts(txs, contract, ALL_RULES)
                if alerts:
                    _append_alerts(alerts, output)
                    for alert in alerts:
                        console.print(
                            f"[{label}] [{alert.severity.value.upper()}] "
                            f"{alert.rule_name}: {alert.message}"
                        )
                else:
                    console.print(f"[{label}] OK - {len(txs)} txs, no alerts")
            except Exception as exc:
                console.print(f"[red][{label}] Error: {exc}[/red]")

        time.sleep(cfg.poll_interval_seconds)


@app.command()
def alerts(
    log_file: Path = typer.Option(ALERTS_LOG, "--file", "-f", help="Alerts log file"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max alerts to show"),
) -> None:
    """Show recent alerts from the local alerts.jsonl log."""
    if not log_file.exists():
        console.print("No alerts log found.")
        raise typer.Exit(0)

    lines = log_file.read_text().strip().splitlines()
    recent = lines[-limit:] if len(lines) > limit else lines

    table = Table(title="Recent Alerts")
    table.add_column("Severity", style="bold")
    table.add_column("Rule")
    table.add_column("Contract")
    table.add_column("Message")
    table.add_column("TX Hash")

    for line in reversed(recent):
        data = json.loads(line)
        severity = data.get("severity", "")
        style = "red" if severity in ("critical", "high") else "yellow"
        table.add_row(
            f"[{style}]{severity.upper()}[/{style}]",
            data.get("rule_name", ""),
            data.get("contract", {}).get("name", ""),
            data.get("message", ""),
            (data.get("tx_hash") or "")[:16],
        )

    console.print(table)


@app.command()
def serve() -> None:
    """Start the MCP server (stdio transport)."""
    from sentinel.mcp_server import create_server

    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    app()
