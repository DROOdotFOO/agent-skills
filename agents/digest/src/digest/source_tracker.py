"""Source credibility tracking over time.

Tracks how well each source's items hold up across consecutive digests.
An item that reappears with sustained or growing engagement is a "hit";
one that vanishes is a "miss". The hit rate becomes a credibility adjustment.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "digest" / "feed.db"


class SourceTracker:
    """Tracks per-source accuracy using the feed memory database."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        if not self.db_path.exists():
            self._conn = None
            return
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._ensure_table()

    def _ensure_table(self) -> None:
        if self._conn is None:
            return
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS source_scores (
                source TEXT NOT NULL,
                topic TEXT NOT NULL,
                hits INTEGER NOT NULL DEFAULT 0,
                misses INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT,
                PRIMARY KEY (source, topic)
            )
        """)
        self._conn.commit()

    def update_scores(self, topic: str) -> dict[str, dict]:
        """Compare the two most recent digests and update source scores.

        For each source in the previous digest, count how many of its items
        reappeared in the latest digest (hits) vs disappeared (misses).

        Returns a dict of {source: {hits, misses, accuracy}} for the update.
        """
        if self._conn is None:
            return {}

        # Get the two most recent digest IDs for this topic
        rows = self._conn.execute(
            "SELECT id FROM digests WHERE topic = ? ORDER BY generated_at DESC LIMIT 2",
            (topic,),
        ).fetchall()

        if len(rows) < 2:
            return {}

        latest_id = rows[0][0]
        previous_id = rows[1][0]

        # Get URLs in latest digest
        latest_urls = {
            r[0]
            for r in self._conn.execute(
                "SELECT url FROM items WHERE digest_id = ?", (latest_id,)
            ).fetchall()
        }

        # Get items from previous digest grouped by source
        prev_items = self._conn.execute(
            "SELECT source, url FROM items WHERE digest_id = ?", (previous_id,)
        ).fetchall()

        source_results: dict[str, dict] = {}
        for source, url in prev_items:
            if source not in source_results:
                source_results[source] = {"hits": 0, "misses": 0}
            if url in latest_urls:
                source_results[source]["hits"] += 1
            else:
                source_results[source]["misses"] += 1

        # Persist to source_scores table
        now = _now()
        for source, counts in source_results.items():
            self._conn.execute(
                """INSERT INTO source_scores (source, topic, hits, misses, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(source, topic) DO UPDATE SET
                     hits = hits + excluded.hits,
                     misses = misses + excluded.misses,
                     updated_at = excluded.updated_at""",
                (source, topic, counts["hits"], counts["misses"], now),
            )
            counts["accuracy"] = _accuracy(counts["hits"], counts["misses"])

        self._conn.commit()
        return source_results

    def get_accuracy(self, source: str, topic: str) -> float:
        """Get the credibility accuracy multiplier for a source+topic.

        Returns a float between 0.5 (unreliable) and 1.5 (very reliable).
        Returns 1.0 (neutral) if no data or insufficient samples.
        """
        if self._conn is None:
            return 1.0

        row = self._conn.execute(
            "SELECT hits, misses FROM source_scores WHERE source = ? AND topic = ?",
            (source, topic),
        ).fetchone()

        if row is None:
            return 1.0

        hits, misses = row
        return _accuracy(hits, misses)

    def get_all_scores(self, topic: str) -> dict[str, dict]:
        """Get accuracy scores for all sources on a topic."""
        if self._conn is None:
            return {}

        rows = self._conn.execute(
            "SELECT source, hits, misses FROM source_scores WHERE topic = ?",
            (topic,),
        ).fetchall()

        result = {}
        for source, hits, misses in rows:
            result[source] = {
                "hits": hits,
                "misses": misses,
                "accuracy": _accuracy(hits, misses),
                "samples": hits + misses,
            }
        return result

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()


def _accuracy(hits: int, misses: int) -> float:
    """Convert hit/miss counts to a 0.5-1.5 multiplier.

    Needs at least 5 samples to move off neutral. Uses a simple
    hit rate mapped linearly: 0% hits -> 0.5, 50% -> 1.0, 100% -> 1.5.
    """
    total = hits + misses
    if total < 5:
        return 1.0
    rate = hits / total
    return 0.5 + rate  # 0% -> 0.5, 100% -> 1.5


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
