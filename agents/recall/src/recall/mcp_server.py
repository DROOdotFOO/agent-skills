"""FastMCP server exposing recall tools for Claude Code integration."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from recall.models import EntryType
from recall.store import Store


def create_server(db_path: Path | None = None) -> FastMCP:
    """Create a FastMCP server with recall tools."""
    mcp = FastMCP(
        "recall",
        instructions=(
            "Knowledge capture and retrieval. Use recall_search to find relevant past "
            "decisions, patterns, gotchas, and insights. Use recall_add to capture new "
            "knowledge worth remembering across sessions."
        ),
    )
    store = Store(db_path=db_path)

    @mcp.tool()
    def recall_add(
        content: str,
        entry_type: str = "insight",
        project: str | None = None,
        tags: str | None = None,
        source: str | None = None,
    ) -> str:
        """Add a knowledge entry to the recall store.

        Args:
            content: The knowledge to capture (decisions, patterns, gotchas, links, insights)
            entry_type: One of: decision, pattern, gotcha, link, insight
            project: Project this relates to (optional)
            tags: Comma-separated tags (optional)
            source: Where this came from (optional)
        """
        from recall.models import Entry

        tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
        entry = Entry(
            content=content,
            entry_type=EntryType(entry_type),
            project=project,
            tags=tag_list,
            source=source,
        )
        result = store.add(entry)
        return f"Added entry #{result.id} ({entry_type})"

    @mcp.tool()
    def recall_search(
        query: str,
        project: str | None = None,
        entry_type: str | None = None,
        tags: str | None = None,
        limit: int = 10,
    ) -> str:
        """Search the recall knowledge base using full-text search.

        Args:
            query: Search query (supports FTS5 syntax: AND, OR, NOT, "exact phrase", prefix*)
            project: Filter by project name (optional)
            entry_type: Filter by type: decision, pattern, gotcha, link, insight (optional)
            tags: Comma-separated tags to filter by (optional)
            limit: Max results to return (default 10)
        """
        et = EntryType(entry_type) if entry_type else None
        tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()] or None
        results = store.search(query, project=project, entry_type=et, tags=tag_list, limit=limit)

        if not results:
            return "No results found."

        lines = []
        for r in results:
            e = r.entry
            meta_parts = [e.entry_type.value]
            if e.project:
                meta_parts.append(f"project:{e.project}")
            if e.tags:
                meta_parts.append(f"tags:{','.join(e.tags)}")
            meta = " | ".join(meta_parts)
            lines.append(f"[#{e.id}] ({meta})\n{e.content}\n")

        return "\n".join(lines)

    @mcp.tool()
    def recall_list(
        project: str | None = None,
        entry_type: str | None = None,
        limit: int = 20,
    ) -> str:
        """List recent knowledge entries.

        Args:
            project: Filter by project name (optional)
            entry_type: Filter by type: decision, pattern, gotcha, link, insight (optional)
            limit: Max entries to return (default 20)
        """
        et = EntryType(entry_type) if entry_type else None
        entries = store.list_entries(project=project, entry_type=et, limit=limit)

        if not entries:
            return "No entries found."

        lines = []
        for e in entries:
            meta_parts = [e.entry_type.value]
            if e.project:
                meta_parts.append(e.project)
            if e.tags:
                meta_parts.append(",".join(e.tags))
            meta = " | ".join(meta_parts)
            preview = e.content[:150].replace("\n", " ")
            lines.append(f"[#{e.id}] ({meta}) {preview}")

        return "\n".join(lines)

    @mcp.tool()
    def recall_get(entry_id: int) -> str:
        """Get a single knowledge entry by ID.

        Args:
            entry_id: The entry ID to retrieve
        """
        entry = store.get(entry_id)
        if entry is None:
            return f"Entry #{entry_id} not found."

        parts = [f"# Entry #{entry.id} ({entry.entry_type.value})"]
        if entry.project:
            parts.append(f"Project: {entry.project}")
        if entry.tags:
            parts.append(f"Tags: {', '.join(entry.tags)}")
        if entry.source:
            parts.append(f"Source: {entry.source}")
        parts.append(f"Created: {entry.created_at}")
        parts.append(f"Accessed: {entry.access_count} times")
        parts.append("")
        parts.append(entry.content)
        return "\n".join(parts)

    @mcp.tool()
    def recall_delete(entry_id: int) -> str:
        """Delete a knowledge entry by ID.

        Args:
            entry_id: The entry ID to delete
        """
        deleted = store.delete(entry_id)
        if deleted:
            return f"Deleted entry #{entry_id}."
        return f"Entry #{entry_id} not found."

    @mcp.tool()
    def recall_stats() -> str:
        """Show recall store statistics (total entries, by type, by project)."""
        s = store.stats()
        parts = [f"Total entries: {s['total']}"]
        if s["by_type"]:
            parts.append("By type:")
            for t, cnt in sorted(s["by_type"].items()):
                parts.append(f"  {t}: {cnt}")
        if s["by_project"]:
            parts.append("By project:")
            for p, cnt in s["by_project"].items():
                parts.append(f"  {p}: {cnt}")
        return "\n".join(parts)

    @mcp.tool()
    def recall_extract(
        days: int = 30,
        project: str | None = None,
        dry_run: bool = True,
    ) -> str:
        """Extract decisions and insights from Claude Code session logs.

        Parses ~/.claude/history.jsonl for decision-indicating messages
        (e.g. "decided to", "don't use", "root cause", "note:") and
        optionally adds them to the recall store.

        Args:
            days: Look back N days (default 30)
            project: Filter by project basename (optional)
            dry_run: If true, show what would be extracted without adding (default true)
        """
        from recall.extract import extract_from_logs

        entries = extract_from_logs(days=days, project=project)

        if not entries:
            return "No matching entries found in session logs."

        lines = []
        for e in entries:
            meta_parts = [e.entry_type.value]
            if e.project:
                meta_parts.append(f"project:{e.project}")
            if e.tags:
                meta_parts.append(f"tags:{','.join(e.tags)}")
            meta = " | ".join(meta_parts)
            preview = e.content[:150].replace("\n", " ")
            lines.append(f"({meta}) {preview}")

        if dry_run:
            lines.insert(0, f"Found {len(entries)} extractable entries (dry run):\n")
            return "\n".join(lines)

        added = 0
        skipped = 0
        for entry in entries:
            existing = store.search(
                f'"{entry.content[:80]}"',
                project=entry.project,
                limit=1,
            )
            if existing and existing[0].entry.content == entry.content:
                skipped += 1
                continue
            store.add(entry)
            added += 1

        lines.insert(0, f"Added {added}, skipped {skipped} duplicates:\n")
        return "\n".join(lines)

    @mcp.tool()
    def recall_stale(days: int = 90, limit: int = 20) -> str:
        """Find stale entries not accessed recently (candidates for pruning).

        Args:
            days: Entries not accessed in this many days are stale (default 90)
            limit: Max entries to return (default 20)
        """
        entries = store.stale(days=days, limit=limit)
        if not entries:
            return "No stale entries."

        lines = []
        for e in entries:
            last = str(e.accessed_at)[:10] if e.accessed_at else "never"
            lines.append(
                f"[#{e.id}] ({e.entry_type.value}) last access: {last} -- {e.content[:100]}"
            )
        return "\n".join(lines)

    return mcp
