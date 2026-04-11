"""Query expansion: translate a topic into platform-specific search strategies.

Raw keyword searches produce noisy digests for narrow technical topics (e.g.
"noir zero knowledge" returns unrelated grants that happen to mention "zero
knowledge"). This module expands topics into structured queries that route
adapters to high-signal sources: specific GitHub orgs/repos, alternate
keywords, topic tags.

Current implementation uses static rules. An LLM-based fallback for unknown
topics is a future extension -- the `expand()` signature is designed to
accommodate it transparently.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExpandedQuery(BaseModel):
    """Structured search query with platform-specific hints."""

    original: str = Field(description="The user's original topic string")
    terms: list[str] = Field(
        default_factory=list,
        description="Generic full-text search terms",
    )
    hn_terms: list[str] = Field(
        default_factory=list,
        description=(
            "HN-specific terms. Algolia full-text search is noisy for short "
            "ambiguous words (e.g. 'noir' matches pinot wine, film noir, astronomy). "
            "Use compound phrases here. If empty, `terms` is used as fallback."
        ),
    )
    github_qualifiers: list[str] = Field(
        default_factory=list,
        description="GitHub search qualifiers like 'org:noir-lang', 'repo:tokio-rs/tokio'",
    )
    github_topics: list[str] = Field(
        default_factory=list,
        description="GitHub topic tags, applied as 'topic:<name>'",
    )

    @property
    def effective_hn_terms(self) -> list[str]:
        """Terms to use for HN searches -- prefer `hn_terms`, fall back to `terms`."""
        return self.hn_terms if self.hn_terms else self.terms

    @property
    def matched_rules(self) -> bool:
        """True if any expansion rule fired beyond the literal topic."""
        return bool(
            self.github_qualifiers or self.github_topics or self.hn_terms or len(self.terms) > 1
        )


# Static expansion rules. Keys are topic fragments matched via case-insensitive
# substring; if any key is found inside the user's topic, its rules are merged.
# New expansions can be added without touching any adapter code.
EXPANSIONS: dict[str, dict[str, Any]] = {
    "noir": {
        # terms drive GitHub fallback; hn_terms must be compound to avoid
        # matching "pinot noir", "film noir", "NOIRLab astronomy", etc.
        "terms": ["noir", "aztec noir", "noir-lang", "barretenberg"],
        "hn_terms": ["aztec noir", "noir-lang", "barretenberg", "noir zk"],
        "github_qualifiers": ["org:noir-lang", "org:AztecProtocol"],
        "github_topics": ["noir-lang", "noir"],
    },
    "aztec": {
        "terms": ["aztec protocol", "aztec network", "aztec noir"],
        "hn_terms": ["aztec protocol", "aztec network", "aztec noir"],
        "github_qualifiers": ["org:AztecProtocol"],
    },
    "rust async": {
        "terms": ["rust async", "tokio", "async-std", "smol runtime"],
        "hn_terms": ["rust async", "tokio rust", "async rust"],
        "github_qualifiers": [
            "repo:tokio-rs/tokio",
            "repo:async-rs/async-std",
            "repo:smol-rs/smol",
        ],
    },
    "claude code skills": {
        "terms": ["claude code skills", "claude-code skill", "claude skills"],
        "hn_terms": ["claude code skill", "claude code skills"],
        "github_topics": ["claude-code", "claude-skills", "anthropic"],
    },
    "solidity": {
        "terms": ["solidity", "smart contract audit", "foundry"],
        "hn_terms": ["solidity smart contract", "smart contract audit", "foundry framework"],
        "github_qualifiers": ["org:foundry-rs", "org:OpenZeppelin"],
        "github_topics": ["solidity", "foundry", "smart-contracts"],
    },
    "elixir": {
        "terms": ["elixir", "phoenix framework"],
        "hn_terms": ["elixir language", "phoenix framework", "elixir lang"],
        "github_qualifiers": ["org:elixir-lang", "org:phoenixframework"],
        "github_topics": ["elixir"],
    },
    "raxol": {
        "terms": ["raxol", "elixir tui", "raxol framework"],
        "hn_terms": ["raxol elixir", "raxol framework", "raxol tui"],
        "github_qualifiers": ["repo:Hydepwns/raxol"],
    },
    "nix": {
        "terms": ["nixos", "nix flakes", "home manager"],
        "hn_terms": ["nixos", "nix flakes", "home manager nix"],
        "github_qualifiers": ["org:NixOS", "org:nix-community"],
        "github_topics": ["nix", "nixos", "nix-flakes"],
    },
    "zig": {
        "terms": ["zig language", "ziglang"],
        "hn_terms": ["zig language", "ziglang", "zig programming"],
        "github_qualifiers": ["org:ziglang"],
        "github_topics": ["zig", "ziglang"],
    },
}


def expand(topic: str) -> ExpandedQuery:
    """Expand a topic into a structured query.

    Matches any EXPANSIONS key that appears as a substring of `topic`
    (case-insensitive) and merges their rules. Always includes the original
    topic in `terms` so adapters have a fallback literal search.
    """
    topic_lower = topic.lower()
    matched: list[dict[str, Any]] = [
        rules for key, rules in EXPANSIONS.items() if key in topic_lower
    ]

    terms: set[str] = {topic}
    hn_terms: set[str] = set()
    qualifiers: set[str] = set()
    topics: set[str] = set()

    for rules in matched:
        terms.update(rules.get("terms", []))
        hn_terms.update(rules.get("hn_terms", []))
        qualifiers.update(rules.get("github_qualifiers", []))
        topics.update(rules.get("github_topics", []))

    return ExpandedQuery(
        original=topic,
        terms=sorted(terms),
        hn_terms=sorted(hn_terms),
        github_qualifiers=sorted(qualifiers),
        github_topics=sorted(topics),
    )


def literal(topic: str) -> ExpandedQuery:
    """Build a no-expansion query that only searches the literal topic.

    Used by the `--no-expansion` CLI flag to compare expanded vs raw results.
    """
    return ExpandedQuery(original=topic, terms=[topic])
