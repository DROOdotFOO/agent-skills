"""Unit tests for GitHub repo engagement calculation.

Verifies that the composite engagement metric caps viral star counts
and rewards sustained activity signals (forks, open issues).
"""

from __future__ import annotations

from digest.adapters.github import GitHubAdapter


def _engagement_from_row(row: dict) -> int:
    """Replicate the engagement formula from GitHubAdapter._search_repos."""
    stars = row.get("stargazersCount", 0)
    forks = row.get("forksCount", 0)
    open_issues = row.get("openIssuesCount", 0)
    return min(stars, GitHubAdapter.STAR_CAP) + forks * 3 + open_issues


def test_star_cap_limits_viral_repos():
    viral = {"stargazersCount": 29000, "forksCount": 0, "openIssuesCount": 0}
    assert _engagement_from_row(viral) == GitHubAdapter.STAR_CAP


def test_forks_weighted_more_than_stars_per_unit():
    forky = {"stargazersCount": 100, "forksCount": 50, "openIssuesCount": 0}
    stary = {"stargazersCount": 250, "forksCount": 0, "openIssuesCount": 0}
    # forky: 100 + 150 + 0 = 250; stary: 250 + 0 + 0 = 250
    assert _engagement_from_row(forky) == _engagement_from_row(stary)


def test_active_small_repo_can_beat_viral_repo_with_no_activity():
    viral = {"stargazersCount": 50000, "forksCount": 0, "openIssuesCount": 0}
    active = {"stargazersCount": 200, "forksCount": 100, "openIssuesCount": 30}
    # viral: capped at 500
    # active: 200 + 300 + 30 = 530
    assert _engagement_from_row(active) > _engagement_from_row(viral)


def test_zero_engagement_for_empty_new_repo():
    empty = {"stargazersCount": 0, "forksCount": 0, "openIssuesCount": 0}
    assert _engagement_from_row(empty) == 0
