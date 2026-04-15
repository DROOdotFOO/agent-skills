"""GitHub adapter using the `gh` CLI for authenticated search."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone

from digest.expansion import ExpandedQuery
from digest.models import Item


class GitHubAdapter:
    name = "github"

    # Repos with more than this many stars have their star count capped in
    # the engagement score. Prevents viral "meme" repos (10K+ stars in days)
    # from dominating over sustained HN discussions and active-but-smaller
    # projects with high fork/issue activity.
    STAR_CAP = 500

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        if shutil.which("gh") is None:
            raise RuntimeError("gh CLI not found. Install from https://cli.github.com")

        since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()

        owners, repos_filter, topics = self._extract_filters(query)
        has_strong_scope = bool(owners or repos_filter or topics)

        # When we have strong qualifiers (org/repo/topic), search for active
        # repos in scope via --updated instead of --created. Strong-scope
        # searches don't need a literal term to match -- the scope is enough.
        # Without qualifiers, filter by --created and require the term to match.
        search_term = "" if has_strong_scope else query.original

        repos = self._search_repos(
            search_term,
            since,
            owners,
            topics,
            limit,
            use_updated=has_strong_scope,
        )
        issues = self._search_issues(
            search_term,
            since,
            owners,
            repos_filter,
            limit,
        )

        seen: dict[str, Item] = {}
        for item in repos + issues:
            seen.setdefault(item.url, item)
        return list(seen.values())

    @staticmethod
    def _extract_filters(
        query: ExpandedQuery,
    ) -> tuple[list[str], list[str], list[str]]:
        """Parse expansion qualifiers into gh CLI flag values.

        Returns (owners, repos, topics). `org:foo` -> owners; `repo:a/b` -> repos.
        Unrecognized qualifiers are ignored (they'd need their own flag).
        """
        owners: list[str] = []
        repos: list[str] = []
        for q in query.github_qualifiers:
            if q.startswith("org:"):
                owners.append(q[len("org:") :])
            elif q.startswith("user:"):
                owners.append(q[len("user:") :])
            elif q.startswith("repo:"):
                repos.append(q[len("repo:") :])
        return owners, repos, list(query.github_topics)

    def _gh_json(self, args: list[str]) -> list[dict]:
        proc = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"gh failed: {proc.stderr.strip()}")
        return json.loads(proc.stdout or "[]")

    def _search_repos(
        self,
        term: str,
        since: str,
        owners: list[str],
        topics: list[str],
        limit: int,
        *,
        use_updated: bool = False,
    ) -> list[Item]:
        fields = (
            "name,fullName,description,url,stargazersCount,forksCount,"
            "openIssuesCount,owner,createdAt,pushedAt,updatedAt"
        )
        args = ["search", "repos"]
        if term:
            args.append(term)

        # When we have strong scope (org/topic), show actively-updated repos
        # in that scope. Without scope, only show newly-created repos matching
        # the term (otherwise we'd return every repo on GitHub touched this month).
        date_flag = "--updated" if use_updated else "--created"
        args.extend([date_flag, f">={since}", "--limit", str(limit), "--json", fields])

        for owner in owners:
            args.extend(["--owner", owner])
        for topic in topics:
            args.extend(["--topic", topic])

        rows = self._gh_json(args)
        return [self._build_repo_item(row) for row in rows]

    def _build_repo_item(self, row: dict) -> Item:
        stars = row.get("stargazersCount", 0)
        forks = row.get("forksCount", 0)
        open_issues = row.get("openIssuesCount", 0)

        # Composite engagement: capped stars + weighted activity signals.
        engagement = min(stars, self.STAR_CAP) + forks * 3 + open_issues

        return Item(
            source=self.name,
            title=f"{row['fullName']}: {row.get('description') or ''}".strip(": "),
            url=row["url"],
            author=row.get("owner", {}).get("login"),
            timestamp=datetime.fromisoformat(row["createdAt"].replace("Z", "+00:00")),
            engagement=engagement,
            raw={
                "kind": "repo",
                "stars": stars,
                "forks": forks,
                "open_issues": open_issues,
                "pushed_at": row.get("pushedAt"),
                "full_name": row.get("fullName"),
            },
        )

    def _search_issues(
        self,
        term: str,
        since: str,
        owners: list[str],
        repos: list[str],
        limit: int,
    ) -> list[Item]:
        fields = "title,url,author,createdAt,commentsCount,repository"
        args = ["search", "issues"]
        if term:
            args.append(term)
        args.extend(["--created", f">={since}", "--limit", str(limit), "--json", fields])
        # `gh search issues` supports --owner and --repo but not --topic.
        # --repo is more specific; if we have repos, prefer them over owners.
        if repos:
            for r in repos:
                args.extend(["--repo", r])
        elif owners:
            for owner in owners:
                args.extend(["--owner", owner])

        rows = self._gh_json(args)
        return [self._build_issue_item(row) for row in rows]

    def _build_issue_item(self, row: dict) -> Item:
        return Item(
            source=self.name,
            title=row["title"],
            url=row["url"],
            author=(row.get("author") or {}).get("login"),
            timestamp=datetime.fromisoformat(row["createdAt"].replace("Z", "+00:00")),
            engagement=row.get("commentsCount", 0),
            raw={"kind": "issue", **row},
        )
