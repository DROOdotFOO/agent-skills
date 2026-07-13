"""Typer CLI for the Regen incident reader / correlator."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from regen.client import RegenClient
from regen.config import RegenConfig
from regen.models import CorrelationKeys

app = typer.Typer(help="Regen: read incidents and correlate them with SigNoz OTel.")
console = Console()


def _client(base_url: str | None) -> RegenClient:
    return RegenClient(RegenConfig.from_env(base_url=base_url))


def _fmt_dt(value) -> str:
    return value.isoformat() if value else "-"


def _print_correlation(keys: CorrelationKeys) -> None:
    console.print(
        f"[bold]Incident #{keys.incident_number}[/bold] {keys.title} "
        f"([{keys.severity}] {keys.status})"
    )
    console.print(f"  window: {_fmt_dt(keys.window_start)}  ->  {_fmt_dt(keys.window_end)}")
    if keys.service_names:
        console.print(f"  service.name: {', '.join(keys.service_names)}")
    for k, v in keys.labels.items():
        console.print(f"  {k} = {v}")
    console.print("\n[bold]SigNoz query hint[/bold] (feed into the signoz MCP):")
    console.print(f"  {keys.signoz_hint}")


@app.command()
def incidents(
    status: str = typer.Option(
        None, "--status", "-s", help="triggered|acknowledged|resolved|canceled"
    ),
    severity: str = typer.Option(None, "--severity", help="critical|high|medium|low"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max incidents"),
    base_url: str = typer.Option(
        None, "--base-url", envvar="REGEN_BASE_URL", help="Regen base URL"
    ),
) -> None:
    """List Regen incidents."""
    try:
        rows = _client(base_url).list_incidents(status=status, severity=severity, limit=limit)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    if not rows:
        console.print("No incidents.")
        return

    table = Table(title="Regen Incidents")
    table.add_column("#", justify="right")
    table.add_column("Severity", style="bold")
    table.add_column("Status")
    table.add_column("Title")
    table.add_column("Created")
    table.add_column("ID")
    for inc in rows:
        style = "red" if inc.severity in ("critical", "high") else "yellow"
        table.add_row(
            str(inc.incident_number),
            f"[{style}]{inc.severity.upper()}[/{style}]",
            inc.status,
            inc.title,
            _fmt_dt(inc.created_at),
            inc.id,
        )
    console.print(table)


@app.command()
def incident(
    incident_id: str = typer.Argument(..., help="Incident UUID or number"),
    base_url: str = typer.Option(
        None, "--base-url", envvar="REGEN_BASE_URL", help="Regen base URL"
    ),
) -> None:
    """Show a single incident with its alerts and timeline."""
    try:
        detail = _client(base_url).get_incident(incident_id)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    if detail is None:
        console.print(f"[red]Incident {incident_id} not found.[/red]")
        raise typer.Exit(1)

    console.print(
        f"[bold]#{detail.incident_number}[/bold] {detail.title} "
        f"([{detail.severity}] {detail.status})"
    )
    console.print(
        f"  triggered={_fmt_dt(detail.triggered_at)} ack={_fmt_dt(detail.acknowledged_at)} "
        f"resolved={_fmt_dt(detail.resolved_at)}"
    )
    if detail.summary:
        console.print(f"  summary: {detail.summary}")
    if detail.ai_summary:
        console.print(f"  ai_summary: {detail.ai_summary}")
    if detail.alerts:
        table = Table(title="Linked Alerts")
        table.add_column("Source")
        table.add_column("Title")
        table.add_column("Labels")
        for alert in detail.alerts:
            labels = ", ".join(f"{k}={v}" for k, v in alert.labels.items())
            table.add_row(alert.source, alert.title, labels)
        console.print(table)


@app.command()
def alerts(
    status: str = typer.Option(None, "--status", "-s", help="Filter by alert status"),
    source: str = typer.Option(None, "--source", help="Filter by source"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max alerts"),
    base_url: str = typer.Option(
        None, "--base-url", envvar="REGEN_BASE_URL", help="Regen base URL"
    ),
) -> None:
    """List ingested alerts."""
    try:
        rows = _client(base_url).list_alerts(status=status, source=source, limit=limit)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    if not rows:
        console.print("No alerts.")
        return

    table = Table(title="Regen Alerts")
    table.add_column("Severity", style="bold")
    table.add_column("Status")
    table.add_column("Title")
    table.add_column("Source")
    table.add_column("Labels")
    for alert in rows:
        labels = ", ".join(f"{k}={v}" for k, v in alert.labels.items())
        table.add_row(alert.severity.upper(), alert.status, alert.title, alert.source, labels)
    console.print(table)


@app.command()
def correlate(
    incident_id: str = typer.Argument(..., help="Incident UUID or number"),
    base_url: str = typer.Option(
        None, "--base-url", envvar="REGEN_BASE_URL", help="Regen base URL"
    ),
) -> None:
    """Extract SigNoz-query join keys from an incident for OTel correlation."""
    try:
        keys = _client(base_url).correlation_keys(incident_id)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    if keys is None:
        console.print(f"[red]Incident {incident_id} not found.[/red]")
        raise typer.Exit(1)
    _print_correlation(keys)


@app.command()
def serve(
    write: bool = typer.Option(
        False, "--write/--no-write", help="Enable write tools (ack/resolve/update)"
    ),
) -> None:
    """Start the MCP server (stdio transport)."""
    from regen.mcp_server import create_server

    # --write forces write mode on; without it, fall back to REGEN_ENABLE_WRITE.
    server = create_server(enable_write=True if write else None)
    server.run(transport="stdio")


if __name__ == "__main__":
    app()
