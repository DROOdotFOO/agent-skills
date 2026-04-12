"""Typer CLI entry point for the recall agent."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from recall.extract import extract_from_logs
from recall.models import Entry, EntryType
from recall.store import Store

app = typer.Typer(help="Knowledge capture and retrieval agent", no_args_is_help=True)
console = Console()
err = Console(stderr=True)


def _store(db: Path | None) -> Store:
    return Store(db_path=db)


def _type_option() -> EntryType | None:
    return None


@app.command()
def add(
    content: Annotated[str, typer.Argument(help="Knowledge to capture")],
    entry_type: Annotated[
        EntryType, typer.Option("--type", "-t", help="Entry type")
    ] = EntryType.INSIGHT,
    project: Annotated[str | None, typer.Option("--project", "-p", help="Project name")] = None,
    tags: Annotated[str | None, typer.Option("--tags", help="Comma-separated tags")] = None,
    source: Annotated[str | None, typer.Option("--source", "-s", help="Source identifier")] = None,
    db: Annotated[Path | None, typer.Option("--db", hidden=True)] = None,
) -> None:
    """Add a knowledge entry."""
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
    entry = Entry(
        content=content, entry_type=entry_type, project=project, tags=tag_list, source=source
    )
    store = _store(db)
    try:
        result = store.add(entry)
    except ValueError as exc:
        store.close()
        err.print(f"[red]Blocked: {exc}[/red]")
        raise typer.Exit(1) from None
    store.close()
    console.print(f"Added entry #{result.id} ({entry_type.value})")


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query (FTS5 syntax)")],
    project: Annotated[str | None, typer.Option("--project", "-p")] = None,
    entry_type: Annotated[EntryType | None, typer.Option("--type", "-t")] = None,
    tags: Annotated[str | None, typer.Option("--tags")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n")] = 20,
    min_relevance: Annotated[
        float | None,
        typer.Option(
            "--min-relevance",
            help="MAD-normalized relevance floor (0.0=median, 1.0=outliers only)",
        ),
    ] = None,
    db: Annotated[Path | None, typer.Option("--db", hidden=True)] = None,
) -> None:
    """Search entries by full-text query."""
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()] or None
    store = _store(db)
    results = store.search(
        query,
        project=project,
        entry_type=entry_type,
        tags=tag_list,
        limit=limit,
        min_relevance=min_relevance,
    )
    store.close()

    if not results:
        err.print("[dim]No results found.[/dim]")
        raise typer.Exit(0)

    table = Table(title=f"Results for '{query}'", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Type", width=10)
    table.add_column("Content", ratio=3)
    table.add_column("Project", width=15)
    table.add_column("Tags", width=20)

    for r in results:
        e = r.entry
        table.add_row(
            str(e.id),
            e.entry_type.value,
            r.snippet or e.content[:120],
            e.project or "",
            ", ".join(e.tags),
        )
    console.print(table)


@app.command("list")
def list_entries(
    project: Annotated[str | None, typer.Option("--project", "-p")] = None,
    entry_type: Annotated[EntryType | None, typer.Option("--type", "-t")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n")] = 50,
    db: Annotated[Path | None, typer.Option("--db", hidden=True)] = None,
) -> None:
    """List recent entries."""
    store = _store(db)
    entries = store.list_entries(project=project, entry_type=entry_type, limit=limit)
    store.close()

    if not entries:
        err.print("[dim]No entries found.[/dim]")
        raise typer.Exit(0)

    table = Table(show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Type", width=10)
    table.add_column("Content", ratio=3)
    table.add_column("Project", width=15)
    table.add_column("Tags", width=20)
    table.add_column("Created", width=12)

    for e in entries:
        created = str(e.created_at)[:10] if e.created_at else ""
        table.add_row(
            str(e.id),
            e.entry_type.value,
            e.content[:120],
            e.project or "",
            ", ".join(e.tags),
            created,
        )
    console.print(table)


@app.command()
def get(
    entry_id: Annotated[int, typer.Argument(help="Entry ID")],
    db: Annotated[Path | None, typer.Option("--db", hidden=True)] = None,
) -> None:
    """Show a single entry by ID."""
    store = _store(db)
    entry = store.get(entry_id)
    store.close()

    if entry is None:
        err.print(f"[red]Entry #{entry_id} not found.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]#{entry.id}[/bold] ({entry.entry_type.value})")
    if entry.project:
        console.print(f"Project: {entry.project}")
    if entry.tags:
        console.print(f"Tags: {', '.join(entry.tags)}")
    if entry.source:
        console.print(f"Source: {entry.source}")
    console.print(f"Created: {entry.created_at}")
    console.print(f"Accessed: {entry.access_count} times")
    console.print()
    console.print(entry.content)


@app.command()
def delete(
    entry_id: Annotated[int, typer.Argument(help="Entry ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
    db: Annotated[Path | None, typer.Option("--db", hidden=True)] = None,
) -> None:
    """Delete an entry by ID."""
    store = _store(db)
    if not force:
        entry = store.get(entry_id)
        if entry is None:
            err.print(f"[red]Entry #{entry_id} not found.[/red]")
            store.close()
            raise typer.Exit(1)
        console.print(f"[dim]{entry.content[:200]}[/dim]")
        if not typer.confirm(f"Delete entry #{entry_id}?"):
            store.close()
            raise typer.Exit(0)

    deleted = store.delete(entry_id)
    store.close()
    if deleted:
        console.print(f"Deleted entry #{entry_id}")
    else:
        err.print(f"[red]Entry #{entry_id} not found.[/red]")
        raise typer.Exit(1)


@app.command()
def stale(
    days: Annotated[int, typer.Option("--days", "-d", help="Days since last access")] = 90,
    limit: Annotated[int, typer.Option("--limit", "-n")] = 20,
    db: Annotated[Path | None, typer.Option("--db", hidden=True)] = None,
) -> None:
    """Show entries not accessed recently (candidates for pruning)."""
    store = _store(db)
    entries = store.stale(days=days, limit=limit)
    store.close()

    if not entries:
        console.print("[green]No stale entries.[/green]")
        raise typer.Exit(0)

    table = Table(title=f"Entries not accessed in {days}+ days", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Type", width=10)
    table.add_column("Content", ratio=3)
    table.add_column("Last access", width=12)
    table.add_column("Accesses", width=8)

    for e in entries:
        last = str(e.accessed_at)[:10] if e.accessed_at else "never"
        table.add_row(str(e.id), e.entry_type.value, e.content[:120], last, str(e.access_count))
    console.print(table)


@app.command()
def stats(
    db: Annotated[Path | None, typer.Option("--db", hidden=True)] = None,
) -> None:
    """Show store statistics."""
    store = _store(db)
    s = store.stats()
    store.close()

    console.print(f"[bold]Total entries:[/bold] {s['total']}")
    if s["by_type"]:
        console.print("[bold]By type:[/bold]")
        for t, cnt in sorted(s["by_type"].items()):
            console.print(f"  {t}: {cnt}")
    if s["by_project"]:
        console.print("[bold]By project:[/bold]")
        for p, cnt in s["by_project"].items():
            console.print(f"  {p}: {cnt}")


@app.command()
def extract(
    days: Annotated[int, typer.Option("--days", "-d", help="Look back N days")] = 30,
    project: Annotated[
        str | None, typer.Option("--project", "-p", help="Filter by project basename")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would be extracted without adding")
    ] = False,
    db: Annotated[Path | None, typer.Option("--db", hidden=True)] = None,
    history: Annotated[Path | None, typer.Option("--history", hidden=True)] = None,
) -> None:
    """Extract decisions and insights from Claude Code session logs."""
    entries = extract_from_logs(days=days, project=project, history_path=history)

    if not entries:
        err.print("[dim]No matching entries found in logs.[/dim]")
        raise typer.Exit(0)

    table = Table(title=f"Extracted {len(entries)} entries (last {days} days)", show_lines=True)
    table.add_column("Type", width=10)
    table.add_column("Content", ratio=3)
    table.add_column("Project", width=15)
    table.add_column("Tags", width=20)
    table.add_column("Source", width=20)

    for e in entries:
        table.add_row(
            e.entry_type.value,
            e.content[:120],
            e.project or "",
            ", ".join(e.tags),
            e.source or "",
        )
    console.print(table)

    if dry_run:
        console.print(f"[dim]Dry run: {len(entries)} entries would be added.[/dim]")
        return

    store = _store(db)
    added = 0
    skipped = 0
    for entry in entries:
        # Skip duplicates by checking for same content and source.
        existing = store.search(
            f'"{entry.content[:80]}"',
            project=entry.project,
            limit=1,
        )
        if existing and existing[0].entry.content == entry.content:
            skipped += 1
            continue
        try:
            store.add(entry)
            added += 1
        except ValueError:
            skipped += 1
    store.close()

    console.print(f"Added {added} entries, skipped {skipped} duplicates.")


@app.command()
def serve(
    db: Annotated[Path | None, typer.Option("--db", hidden=True)] = None,
) -> None:
    """Start the MCP server (stdio transport)."""
    from recall.mcp_server import create_server

    server = create_server(db_path=db)
    server.run(transport="stdio")


if __name__ == "__main__":
    app()
