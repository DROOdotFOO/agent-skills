"""YouTube adapter via yt-dlp (no API key required).

Uses yt-dlp's YouTube search (ytsearchN:query) with --flat-playlist for fast
metadata-only fetches. Engagement is based on view_count (always available in
flat mode) plus like_count and comment_count when present.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone

from digest.expansion import ExpandedQuery
from digest.models import Item


class YouTubeAdapter:
    name = "youtube"

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        """Fetch videos matching query terms via yt-dlp search.

        Runs one search per term and dedupes by video ID. Uses --flat-playlist
        for speed (metadata from search results page, no per-video fetch).
        """
        if shutil.which("yt-dlp") is None:
            raise RuntimeError("yt-dlp not found. Install with: brew install yt-dlp")

        terms = query.terms
        per_term_limit = max(limit // max(len(terms), 1), 5)

        seen: dict[str, Item] = {}
        for term in terms:
            results = self._search(term, per_term_limit)
            for entry in results:
                video_id = entry.get("id", "")
                if video_id and video_id not in seen:
                    item = self._build_item(entry)
                    if item is not None:
                        seen[video_id] = item

        return list(seen.values())[:limit]

    def _search(self, term: str, limit: int) -> list[dict]:
        proc = subprocess.run(
            [
                "yt-dlp",
                f"ytsearch{limit}:{term}",
                "--dump-json",
                "--flat-playlist",
                "--no-warnings",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if proc.returncode != 0:
            return []

        results = []
        for line in proc.stdout.strip().splitlines():
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return results

    def _build_item(self, entry: dict) -> Item | None:
        video_id = entry.get("id", "")
        title = entry.get("title", "")
        if not video_id or not title:
            return None

        view_count = entry.get("view_count") or 0
        like_count = entry.get("like_count") or 0
        comment_count = entry.get("comment_count") or 0

        # Views are orders of magnitude larger than other signals.
        # Scale down so a 100K-view video ~ a 1K-engagement HN post.
        engagement = view_count // 100 + like_count + comment_count

        upload_date = entry.get("upload_date", "")
        if upload_date and len(upload_date) == 8:
            ts = datetime(
                int(upload_date[:4]),
                int(upload_date[4:6]),
                int(upload_date[6:8]),
                tzinfo=timezone.utc,
            )
        else:
            ts = datetime.now(timezone.utc)

        return Item(
            source=self.name,
            title=title,
            url=f"https://www.youtube.com/watch?v={video_id}",
            author=entry.get("uploader") or entry.get("channel"),
            timestamp=ts,
            engagement=engagement,
            raw={
                "video_id": video_id,
                "view_count": view_count,
                "like_count": like_count,
                "comment_count": comment_count,
                "duration": entry.get("duration"),
                "channel": entry.get("channel"),
            },
        )
