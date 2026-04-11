"""Snapshot.org governance adapter via GraphQL API (no auth required).

Fetches DAO governance proposals from Snapshot's hub. Supports filtering by
specific spaces (e.g. "aave.eth", "ens.eth") via expansion qualifiers with
a "space:" prefix. Generic searches fetch recent proposals and filter
client-side by title/body matching. Rate limit: 60 req/min.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from digest.expansion import ExpandedQuery
from digest.models import Item

GRAPHQL_URL = "https://hub.snapshot.org/graphql"

PROPOSALS_QUERY = """
query Proposals($first: Int!, $where: ProposalWhere, $orderBy: String, $orderDirection: OrderDirection) {
  proposals(first: $first, where: $where, orderBy: $orderBy, orderDirection: $orderDirection) {
    id
    title
    body
    state
    author
    created
    end
    scores_total
    votes
    space {
      id
      name
    }
  }
}
"""


class SnapshotAdapter:
    name = "snapshot"

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        """Fetch proposals matching query terms within a time window.

        Extracts space IDs from github_qualifiers with a "space:" prefix.
        Falls back to fetching recent proposals and filtering client-side
        by title/body substring match against query terms.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)
        spaces = self._extract_spaces(query)
        terms = query.terms

        where: dict = {"created_gte": int(since.timestamp())}
        if spaces:
            where["space_in"] = spaces

        proposals = self._query_proposals(where, limit)

        if not spaces:
            proposals = self._filter_by_terms(proposals, terms)

        seen: dict[str, Item] = {}
        for proposal in proposals:
            pid = proposal["id"]
            if pid not in seen:
                seen[pid] = self._build_item(proposal)

        return list(seen.values())[:limit]

    @staticmethod
    def _extract_spaces(query: ExpandedQuery) -> list[str]:
        """Pull space IDs from qualifiers prefixed with 'space:'."""
        return [q.removeprefix("space:") for q in query.github_qualifiers if q.startswith("space:")]

    @staticmethod
    def _filter_by_terms(proposals: list[dict], terms: list[str]) -> list[dict]:
        """Keep proposals where any term appears in title or body."""
        results = []
        for p in proposals:
            title = (p.get("title") or "").lower()
            body = (p.get("body") or "").lower()
            text = f"{title} {body}"
            if any(term.lower() in text for term in terms):
                results.append(p)
        return results

    def _query_proposals(self, where: dict, limit: int) -> list[dict]:
        payload = {
            "query": PROPOSALS_QUERY,
            "variables": {
                "first": min(limit, 100),
                "where": where,
                "orderBy": "created",
                "orderDirection": "desc",
            },
        }
        response = httpx.post(GRAPHQL_URL, json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("proposals", [])

    def _build_item(self, proposal: dict) -> Item:
        votes = proposal.get("votes") or 0
        scores_total = proposal.get("scores_total") or 0
        space = proposal.get("space") or {}
        space_id = space.get("id", "")
        return Item(
            source=self.name,
            title=proposal.get("title") or "",
            url=f"https://snapshot.org/#/{space_id}/proposal/{proposal['id']}",
            author=proposal.get("author"),
            timestamp=datetime.fromtimestamp(proposal.get("created", 0), tz=timezone.utc),
            engagement=votes + int(scores_total),
            raw={
                "space_id": space_id,
                "space_name": space.get("name"),
                "state": proposal.get("state"),
                "votes": votes,
                "scores_total": scores_total,
                "end": proposal.get("end"),
            },
        )
