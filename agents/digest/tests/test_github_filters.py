"""Tests for GitHub adapter filter extraction from expanded queries."""

from __future__ import annotations

from digest.adapters.github import GitHubAdapter
from digest.expansion import ExpandedQuery


def test_extract_org_qualifiers_to_owners():
    query = ExpandedQuery(
        original="noir",
        terms=["noir"],
        github_qualifiers=["org:noir-lang", "org:AztecProtocol"],
    )
    owners, repos, topics = GitHubAdapter._extract_filters(query)
    assert owners == ["noir-lang", "AztecProtocol"]
    assert repos == []
    assert topics == []


def test_extract_repo_qualifier():
    query = ExpandedQuery(
        original="async",
        terms=["async"],
        github_qualifiers=["repo:tokio-rs/tokio"],
    )
    owners, repos, topics = GitHubAdapter._extract_filters(query)
    assert owners == []
    assert repos == ["tokio-rs/tokio"]


def test_extract_user_qualifier_maps_to_owner():
    query = ExpandedQuery(
        original="foo",
        terms=["foo"],
        github_qualifiers=["user:droo"],
    )
    owners, _, _ = GitHubAdapter._extract_filters(query)
    assert owners == ["droo"]


def test_topics_passed_through():
    query = ExpandedQuery(
        original="solidity",
        terms=["solidity"],
        github_topics=["solidity", "foundry"],
    )
    _, _, topics = GitHubAdapter._extract_filters(query)
    assert topics == ["solidity", "foundry"]


def test_unknown_qualifier_ignored():
    query = ExpandedQuery(
        original="x",
        terms=["x"],
        github_qualifiers=["license:mit"],  # not currently parsed
    )
    owners, repos, _ = GitHubAdapter._extract_filters(query)
    assert owners == []
    assert repos == []


def test_mixed_qualifiers():
    query = ExpandedQuery(
        original="mix",
        terms=["mix"],
        github_qualifiers=["org:foo", "repo:bar/baz"],
        github_topics=["tag"],
    )
    owners, repos, topics = GitHubAdapter._extract_filters(query)
    assert owners == ["foo"]
    assert repos == ["bar/baz"]
    assert topics == ["tag"]
