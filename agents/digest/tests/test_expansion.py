"""Unit tests for query expansion rules."""

from __future__ import annotations

from digest.expansion import ExpandedQuery, expand, literal


def test_literal_no_expansion():
    q = literal("some random topic")
    assert q.original == "some random topic"
    assert q.terms == ["some random topic"]
    assert q.github_qualifiers == []
    assert q.matched_rules is False


def test_unknown_topic_falls_back_to_literal():
    q = expand("some completely unknown topic xyz")
    assert q.terms == ["some completely unknown topic xyz"]
    assert q.github_qualifiers == []
    assert q.matched_rules is False


def test_noir_expansion_via_substring():
    q = expand("noir zero knowledge")
    # Original topic preserved as a search term
    assert "noir zero knowledge" in q.terms
    # Noir-specific expansion terms added
    assert "noir-lang" in q.terms
    assert "barretenberg" in q.terms
    # GitHub scoping to relevant orgs
    assert "org:noir-lang" in q.github_qualifiers
    assert "org:AztecProtocol" in q.github_qualifiers
    assert q.matched_rules is True


def test_case_insensitive_matching():
    q_lower = expand("NOIR circuits")
    assert "org:noir-lang" in q_lower.github_qualifiers


def test_multiple_rules_merge():
    # "aztec noir" should match both "noir" and "aztec" rules
    q = expand("aztec noir performance")
    # Both aztec and noir expansions contribute
    assert "org:AztecProtocol" in q.github_qualifiers
    assert "org:noir-lang" in q.github_qualifiers


def test_claude_code_skills_expansion():
    q = expand("claude code skills")
    assert "claude-code" in q.github_topics
    assert "anthropic" in q.github_topics


def test_deduplicated_and_sorted():
    q = expand("noir")
    # No duplicates
    assert len(q.terms) == len(set(q.terms))
    assert len(q.github_qualifiers) == len(set(q.github_qualifiers))
    # Sorted for stable output
    assert q.terms == sorted(q.terms)
    assert q.github_qualifiers == sorted(q.github_qualifiers)


def test_expanded_query_model_fields():
    q = ExpandedQuery(
        original="test",
        terms=["test"],
        github_qualifiers=["org:foo"],
    )
    assert q.matched_rules is True  # has a qualifier
