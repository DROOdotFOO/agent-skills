"""Feed memory -- SQLite storage for past digest results."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from digest.models import DigestResult

DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "digest" / "feed.db"


class FeedMemory:
    """Stores past digest results for differential comparison."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS digests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                days INTEGER NOT NULL,
                item_count INTEGER NOT NULL,
                narrative TEXT,
                generated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                digest_id INTEGER NOT NULL REFERENCES digests(id),
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                engagement INTEGER NOT NULL DEFAULT 0,
                timestamp TEXT,
                raw_json TEXT,
                UNIQUE(digest_id, url)
            );

            CREATE INDEX IF NOT EXISTS idx_items_url ON items(url);
            CREATE INDEX IF NOT EXISTS idx_digests_topic ON digests(topic);
        """)
        self._conn.commit()

    def store(self, result: DigestResult) -> int:
        """Store a digest result. Returns the digest ID."""
        cur = self._conn.execute(
            "INSERT INTO digests (topic, days, item_count, narrative, generated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                result.topic,
                result.days,
                len(result.items),
                result.narrative,
                result.generated_at.isoformat(),
            ),
        )
        digest_id = cur.lastrowid

        for item in result.items:
            self._conn.execute(
                "INSERT OR IGNORE INTO items "
                "(digest_id, source, title, url, engagement, timestamp, raw_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    digest_id,
                    item.source,
                    item.title,
                    item.url,
                    item.engagement,
                    item.timestamp.isoformat() if item.timestamp else None,
                    json.dumps(item.raw),
                ),
            )

        self._conn.commit()
        return digest_id

    def previous_urls(self, topic: str, lookback: int = 3) -> set[str]:
        """Get URLs from the last N digests for a topic."""
        rows = self._conn.execute(
            "SELECT i.url FROM items i "
            "JOIN digests d ON i.digest_id = d.id "
            "WHERE d.topic = ? "
            "ORDER BY d.generated_at DESC "
            "LIMIT ?",
            (topic, lookback * 100),
        ).fetchall()
        return {row[0] for row in rows}

    def url_appearances(self, topic: str, url: str) -> int:
        """Count how many past digests for this topic included this URL."""
        row = self._conn.execute(
            "SELECT COUNT(DISTINCT d.id) FROM items i "
            "JOIN digests d ON i.digest_id = d.id "
            "WHERE d.topic = ? AND i.url = ?",
            (topic, url),
        ).fetchone()
        return row[0] if row else 0

    def engagement_trend(self, topic: str, url: str) -> list[int]:
        """Get engagement scores for a URL across past digests (oldest first)."""
        rows = self._conn.execute(
            "SELECT i.engagement FROM items i "
            "JOIN digests d ON i.digest_id = d.id "
            "WHERE d.topic = ? AND i.url = ? "
            "ORDER BY d.generated_at ASC",
            (topic, url),
        ).fetchall()
        return [row[0] for row in rows]

    def digest_count(self, topic: str) -> int:
        """How many digests have been stored for this topic."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM digests WHERE topic = ?",
            (topic,),
        ).fetchone()
        return row[0] if row else 0

    def close(self) -> None:
        self._conn.close()
