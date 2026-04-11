"""Bridge between digest and recall agents.

Two directions:
1. store_to_recall: persist digest highlights as recall entries
2. fetch_from_recall: pull historical context for a topic
"""

from __future__ import annotations

from pathlib import Path

from digest.models import DigestResult

RECALL_DB_PATH = Path.home() / ".local" / "share" / "recall" / "recall.db"


def recall_available(db_path: Path | None = None) -> bool:
    """Check if the recall store exists and is accessible."""
    path = db_path or RECALL_DB_PATH
    return path.exists()


def store_to_recall(
    result: DigestResult,
    *,
    top_n: int = 5,
    db_path: Path | None = None,
) -> int:
    """Store top digest items as recall entries.

    Creates one 'link' entry per top item, tagged with the topic and source.
    Returns the number of entries added (skips duplicates by URL).
    """
    try:
        from recall.models import Entry, EntryType
        from recall.store import Store
    except ImportError:
        return 0

    store = Store(db_path=db_path)
    added = 0

    for item in result.items[:top_n]:
        # Check for existing entry with same URL
        existing = store.search(
            f'"{item.url}"',
            project=result.topic,
            limit=1,
        )
        if existing and item.url in existing[0].entry.content:
            continue

        content = (
            f"{item.title}\n{item.url}\n\nSource: {item.source}, engagement: {item.engagement}"
        )
        tags = [result.topic, item.source, "digest"]

        entry = Entry(
            content=content,
            entry_type=EntryType.LINK,
            project=result.topic,
            tags=tags,
            source=f"digest:{result.topic}",
        )
        store.add(entry)
        added += 1

    store.close()
    return added


def fetch_from_recall(
    topic: str,
    *,
    limit: int = 10,
    db_path: Path | None = None,
) -> list[dict[str, str]]:
    """Fetch relevant recall entries for a topic.

    Returns simplified dicts with content, type, and tags for
    injection into digest context or synthesis prompts.
    """
    try:
        from recall.store import Store
    except ImportError:
        return []

    if not recall_available(db_path):
        return []

    store = Store(db_path=db_path)
    results = store.search(topic, limit=limit)
    store.close()

    entries = []
    for r in results:
        e = r.entry
        entries.append(
            {
                "content": e.content,
                "type": e.entry_type.value,
                "tags": ",".join(e.tags) if e.tags else "",
                "project": e.project or "",
            }
        )

    return entries


def format_recall_context(entries: list[dict[str, str]]) -> str:
    """Format recall entries as context for digest synthesis."""
    if not entries:
        return ""

    lines = ["## Historical context (from recall)\n"]
    for e in entries:
        entry_type = e["type"]
        content = e["content"][:200]
        lines.append(f"- [{entry_type}] {content}")

    return "\n".join(lines)
