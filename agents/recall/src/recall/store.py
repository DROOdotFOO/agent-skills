"""SQLite + FTS5 storage backend for recall entries."""

from __future__ import annotations

import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path

from recall.models import Entry, EntryType, SearchResult

DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "recall" / "recall.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    entry_type TEXT NOT NULL DEFAULT 'insight',
    project TEXT,
    tags TEXT DEFAULT '',
    source TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    accessed_at TEXT,
    access_count INTEGER DEFAULT 0
);

CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    content,
    tags,
    project,
    content='entries',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Triggers to keep FTS index in sync with entries table
CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
    INSERT INTO entries_fts(rowid, content, tags, project)
    VALUES (new.id, new.content, new.tags, new.project);
END;

CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, content, tags, project)
    VALUES ('delete', old.id, old.content, old.tags, old.project);
END;

CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, content, tags, project)
    VALUES ('delete', old.id, old.content, old.tags, old.project);
    INSERT INTO entries_fts(rowid, content, tags, project)
    VALUES (new.id, new.content, new.tags, new.project);
END;
"""


class Store:
    """SQLite + FTS5 knowledge store."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.executescript(SCHEMA)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def add(self, entry: Entry) -> Entry:
        """Insert a new entry and return it with its ID."""
        now = self._now()
        cursor = self.conn.execute(
            "INSERT INTO entries"
            " (content, entry_type, project, tags, source, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                entry.content,
                entry.entry_type.value,
                entry.project,
                entry.tags_str,
                entry.source,
                now,
                now,
            ),
        )
        self.conn.commit()
        entry.id = cursor.lastrowid
        entry.created_at = now
        entry.updated_at = now
        return entry

    def get(self, entry_id: int) -> Entry | None:
        """Get a single entry by ID, updating access tracking."""
        now = self._now()
        self.conn.execute(
            "UPDATE entries SET accessed_at = ?, access_count = access_count + 1 WHERE id = ?",
            (now, entry_id),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if row is None:
            return None
        return Entry.from_row(dict(row))

    @staticmethod
    def _sanitize_fts_query(query: str) -> str:
        """Wrap each token in quotes to avoid FTS5 syntax errors on hyphens etc."""
        tokens = query.split()
        sanitized = []
        for token in tokens:
            # Preserve explicit FTS5 operators
            if token.upper() in ("AND", "OR", "NOT"):
                sanitized.append(token.upper())
            elif token.startswith('"') and token.endswith('"'):
                sanitized.append(token)
            else:
                sanitized.append(f'"{token}"')
        return " ".join(sanitized)

    @staticmethod
    def _mad_filter(results: list[SearchResult], min_relevance: float) -> list[SearchResult]:
        """Filter results using MAD-normalized thresholding on FTS5 rank scores.

        Keeps results whose rank is below (more relevant than) median - min_relevance * MAD.
        FTS5 ranks are negative: lower (more negative) = more relevant.
        """
        if len(results) < 2:
            return results
        ranks = [r.rank for r in results]
        med = statistics.median(ranks)
        mad = statistics.median([abs(r - med) for r in ranks])
        if mad == 0:
            return results
        threshold = med - min_relevance * mad
        return [r for r in results if r.rank <= threshold]

    def search(
        self,
        query: str,
        *,
        project: str | None = None,
        entry_type: EntryType | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
        min_relevance: float | None = None,
    ) -> list[SearchResult]:
        """Full-text search with optional filters. Returns results ranked by relevance.

        When min_relevance is set, applies MAD-normalized thresholding to drop
        weak matches. A value of 0.0 keeps above-median results; 1.0 keeps only
        clear outliers. Inspired by Latent Briefing (Ramp Labs) adaptive compaction.
        """
        fts_query = self._sanitize_fts_query(query)
        sql = """
            SELECT e.*, entries_fts.rank,
                   snippet(entries_fts, 0, '>>>', '<<<', '...', 32) as snippet
            FROM entries_fts
            JOIN entries e ON e.id = entries_fts.rowid
            WHERE entries_fts MATCH ?
        """
        params: list = [fts_query]

        if project:
            sql += " AND e.project = ?"
            params.append(project)
        if entry_type:
            sql += " AND e.entry_type = ?"
            params.append(entry_type.value)
        if tags:
            for tag in tags:
                sql += " AND e.tags LIKE ?"
                params.append(f"%{tag}%")

        sql += " ORDER BY entries_fts.rank LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(sql, params).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            rank = d.pop("rank")
            snippet = d.pop("snippet")
            entry = Entry.from_row(d)
            results.append(SearchResult(entry=entry, rank=rank, snippet=snippet))

        if min_relevance is not None:
            results = self._mad_filter(results, min_relevance)

        return results

    def list_entries(
        self,
        *,
        project: str | None = None,
        entry_type: EntryType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Entry]:
        """List entries with optional filters, newest first."""
        sql = "SELECT * FROM entries WHERE 1=1"
        params: list = []

        if project:
            sql += " AND project = ?"
            params.append(project)
        if entry_type:
            sql += " AND entry_type = ?"
            params.append(entry_type.value)

        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self.conn.execute(sql, params).fetchall()
        return [Entry.from_row(dict(row)) for row in rows]

    def update(
        self, entry_id: int, content: str | None = None, tags: list[str] | None = None
    ) -> Entry | None:
        """Update an existing entry's content and/or tags."""
        existing = self.conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if existing is None:
            return None

        now = self._now()
        updates = ["updated_at = ?"]
        params: list = [now]

        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if tags is not None:
            updates.append("tags = ?")
            params.append(",".join(tags))

        params.append(entry_id)
        self.conn.execute(f"UPDATE entries SET {', '.join(updates)} WHERE id = ?", params)
        self.conn.commit()
        return self.get(entry_id)

    def delete(self, entry_id: int) -> bool:
        """Delete an entry by ID. Returns True if it existed."""
        cursor = self.conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def stale(self, *, days: int = 90, limit: int = 20) -> list[Entry]:
        """Find entries not accessed in `days` days, ordered oldest-access-first."""
        cutoff = datetime.now(timezone.utc).isoformat()
        sql = """
            SELECT * FROM entries
            WHERE accessed_at IS NULL
               OR accessed_at < datetime(?, '-' || ? || ' days')
            ORDER BY COALESCE(accessed_at, created_at) ASC
            LIMIT ?
        """
        rows = self.conn.execute(sql, (cutoff, days, limit)).fetchall()
        return [Entry.from_row(dict(row)) for row in rows]

    def stats(self) -> dict:
        """Return summary statistics about the store."""
        total = self.conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        by_type = {}
        for row in self.conn.execute(
            "SELECT entry_type, COUNT(*) as cnt FROM entries GROUP BY entry_type"
        ).fetchall():
            by_type[row["entry_type"]] = row["cnt"]
        by_project = {}
        for row in self.conn.execute(
            "SELECT COALESCE(project, '(none)') as proj, COUNT(*) as cnt"
            " FROM entries GROUP BY project ORDER BY cnt DESC LIMIT 10"
        ).fetchall():
            by_project[row["proj"]] = row["cnt"]
        return {"total": total, "by_type": by_type, "by_project": by_project}
