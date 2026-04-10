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
        )

    if query.matched_rules:
        err.print(f"[dim]Expanded query:[/dim] terms={query.terms}")
        if query.github_qualifiers:
            err.print(f"[dim]GitHub qualifiers:[/dim] {query.github_qualifiers}")
        if query.github_topics:
            err.print(f"[dim]GitHub topics:[/dim] {query.github_topics}")
    elif not no_expansion:
        err.print(f"[dim]No expansion rules matched '{topic}' -- using literal search.[/dim]")

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


if __name__ == "__main__":
    app()
