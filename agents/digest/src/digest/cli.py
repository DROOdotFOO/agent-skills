"""Typer CLI entry point for the digest agent."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from digest.adapters import ADAPTERS
from digest.models import DigestRequest
from digest.output import print_terminal, to_markdown
from digest.pipeline import run

app = typer.Typer(help="Multi-platform activity digest agent", no_args_is_help=True)
console = Console()
err = Console(stderr=True)


@app.command()
def generate(
    topic: Annotated[str, typer.Argument(help="Topic to digest")],
    days: Annotated[int, typer.Option("--days", "-d", help="Lookback window in days")] = 30,
    platforms: Annotated[
        str,
        typer.Option(
            "--platforms",
            "-p",
            help=f"Comma-separated platforms. Available: {','.join(ADAPTERS)}",
        ),
    ] = "hn,github",
    max_items: Annotated[
        int,
        typer.Option("--max-items", "-n", help="Max items per platform"),
    ] = 50,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write markdown to file instead of terminal"),
    ] = None,
    no_synthesis: Annotated[
        bool,
        typer.Option("--no-synthesis", help="Skip Claude synthesis; just rank and print items"),
    ] = False,
    no_expansion: Annotated[
        bool,
        typer.Option("--no-expansion", help="Skip query expansion; search topic literally"),
    ] = False,
    remember: Annotated[
        bool,
        typer.Option("--remember", help="Store digest in feed memory for differential tracking"),
    ] = False,
    diff: Annotated[
        bool,
        typer.Option("--diff", help="Show differential: new/accelerating/ongoing/declining"),
    ] = False,
    view: Annotated[
        str | None,
        typer.Option(
            "--view",
            help="Structured view: timeline, controversy, tags, sources, all",
        ),
    ] = None,
) -> None:
    """Generate a digest for TOPIC."""
    platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
    unknown = set(platform_list) - set(ADAPTERS)
    if unknown:
        err.print(f"[red]Unknown platforms:[/red] {', '.join(unknown)}")
        raise typer.Exit(1)

    request = DigestRequest(
        topic=topic,
        days=days,
        platforms=platform_list,
        max_items_per_platform=max_items,
    )

    status_msg = (
        f"Fetching and ranking items for '{topic}'..."
        if no_synthesis
        else f"Fetching and synthesizing digest for '{topic}'..."
    )
    with console.status(status_msg):
        result, query = run(
            request,
            synthesize_narrative=not no_synthesis,
            use_expansion=not no_expansion,
            store_memory=remember,
        )

    if query.matched_rules:
        err.print(f"[dim]Expanded query:[/dim] terms={query.terms}")
        if query.github_qualifiers:
            err.print(f"[dim]GitHub qualifiers:[/dim] {query.github_qualifiers}")
        if query.github_topics:
            err.print(f"[dim]GitHub topics:[/dim] {query.github_topics}")
    elif not no_expansion:
        err.print(f"[dim]No expansion rules matched '{topic}' -- using literal search.[/dim]")

    if view:
        from digest.views import (
            all_views,
            controversy_view,
            source_breakdown_view,
            tag_trends_view,
            timeline_view,
        )

        view_funcs = {
            "timeline": timeline_view,
            "controversy": controversy_view,
            "tags": tag_trends_view,
            "sources": source_breakdown_view,
            "all": all_views,
        }
        func = view_funcs.get(view)
        if func is None:
            err.print(f"[red]Unknown view: {view}[/red] (choose: {', '.join(view_funcs)})")
            raise typer.Exit(1)

        view_text = func(result)
        if output:
            output.write_text(view_text)
            err.print(f"[green]Wrote {view} view to[/green] {output}")
        else:
            from rich.markdown import Markdown

            console.print(Markdown(view_text))
        return

    if diff:
        from digest.diff import classify_items, format_differential
        from digest.memory import FeedMemory

        mem = FeedMemory()
        if mem.digest_count(topic) == 0:
            err.print("[dim]No previous digests found -- all items shown as new.[/dim]")
        classified = classify_items(result, mem)
        mem.close()
        diff_text = format_differential(classified)
        if output:
            output.write_text(to_markdown(result) + "\n\n---\n\n" + diff_text)
            err.print(f"[green]Wrote differential digest to[/green] {output}")
        else:
            from rich.markdown import Markdown

            console.print(Markdown(diff_text))
        return

    if output:
        output.write_text(to_markdown(result))
        err.print(f"[green]Wrote digest to[/green] {output}")
    else:
        print_terminal(result)


@app.command("list-platforms")
def list_platforms() -> None:
    """List available platform adapters."""
    for name in ADAPTERS:
        console.print(f"  {name}")


@app.command()
def watch(
    config: Annotated[
        Path,
        typer.Option("--config", "-f", help="TOML config file for watched topics"),
    ] = Path("digest-watch.toml"),
    once: Annotated[
        bool,
        typer.Option("--once", help="Run a single watch cycle then exit"),
    ] = False,
) -> None:
    """Watch topics and alert on threshold crossings."""
    from digest.watcher import WatchConfig, watch_loop, watch_once

    if not config.exists():
        err.print(f"[red]Config file not found:[/red] {config}")
        raise typer.Exit(1)

    cfg = WatchConfig.from_toml(config)
    if not cfg.topics:
        err.print("[red]No topics defined in config.[/red]")
        raise typer.Exit(1)

    err.print(
        f"[bold]Watching {len(cfg.topics)} topic(s)[/bold] "
        f"every {cfg.poll_interval_minutes}m "
        f"(synthesis={'on' if cfg.synthesize else 'off'})"
    )

    if once:
        watch_once(cfg, console_print=console.print)
    else:
        try:
            watch_loop(cfg, console_print=console.print)
        except KeyboardInterrupt:
            err.print("\n[dim]Watch stopped.[/dim]")


@app.command()
def alerts(
    log_file: Annotated[
        Path | None,
        typer.Option("--file", "-f", help="Alert log path"),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Max alerts to show"),
    ] = 20,
) -> None:
    """Show recent digest alerts."""
    from digest.notifier import read_log

    recent = read_log(log_file, limit=limit)
    if not recent:
        console.print("[dim]No alerts found.[/dim]")
        return

    from rich.table import Table

    table = Table(title=f"Recent Digest Alerts ({len(recent)})")
    table.add_column("Severity", style="bold")
    table.add_column("Topic")
    table.add_column("Rule")
    table.add_column("Message")
    table.add_column("Time")

    severity_colors = {
        "critical": "red bold",
        "high": "red",
        "medium": "yellow",
        "low": "blue",
        "info": "dim",
    }

    for alert in recent:
        color = severity_colors.get(alert.severity.value, "")
        table.add_row(
            f"[{color}]{alert.severity.value.upper()}[/{color}]",
            alert.topic,
            alert.rule,
            alert.message,
            alert.timestamp.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


@app.command()
def serve() -> None:
    """Start the MCP server (stdio transport)."""
    from digest.mcp_server import create_server

    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    app()
