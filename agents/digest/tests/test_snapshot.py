"""Unit tests for Snapshot adapter engagement and item building."""

from __future__ import annotations

from digest.adapters.snapshot import SnapshotAdapter
from digest.expansion import ExpandedQuery


def _build(proposal: dict) -> dict:
    """Build an Item from a Snapshot proposal dict and return raw + engagement."""
    adapter = SnapshotAdapter()
    item = adapter._build_item(proposal)
    return {"engagement": item.engagement, "raw": item.raw, "url": item.url}


def _proposal(**overrides: object) -> dict:
    """Minimal valid proposal with sensible defaults."""
    base: dict = {
        "id": "0xabc123",
        "title": "Test Proposal",
        "body": "A test body",
        "state": "active",
        "author": "0x1234",
        "created": 1700000000,
        "end": 1700086400,
        "scores_total": 0,
        "votes": 0,
        "space": {"id": "aave.eth", "name": "Aave"},
    }
    base.update(overrides)
    return base


def test_engagement_combines_votes_and_scores():
    result = _build(_proposal(votes=120, scores_total=500))
    assert result["engagement"] == 620


def test_engagement_zero_for_empty_proposal():
    result = _build(_proposal(votes=0, scores_total=0))
    assert result["engagement"] == 0


def test_engagement_with_float_scores_total():
    result = _build(_proposal(votes=10, scores_total=99.7))
    assert result["engagement"] == 109


def test_url_includes_space_and_proposal_id():
    result = _build(_proposal())
    assert result["url"] == "https://snapshot.org/#/aave.eth/proposal/0xabc123"


def test_raw_includes_space_and_state():
    result = _build(_proposal(state="closed"))
    assert result["raw"]["space_id"] == "aave.eth"
    assert result["raw"]["space_name"] == "Aave"
    assert result["raw"]["state"] == "closed"


def test_raw_includes_votes_and_scores():
    result = _build(_proposal(votes=42, scores_total=1000))
    assert result["raw"]["votes"] == 42
    assert result["raw"]["scores_total"] == 1000


def test_extract_spaces_from_qualifiers():
    query = ExpandedQuery(
        original="aave governance",
        terms=["aave governance"],
        github_qualifiers=["space:aave.eth", "space:ens.eth", "org:aave"],
    )
    spaces = SnapshotAdapter._extract_spaces(query)
    assert spaces == ["aave.eth", "ens.eth"]


def test_extract_spaces_empty_when_no_prefix():
    query = ExpandedQuery(
        original="defi",
        terms=["defi"],
        github_qualifiers=["org:uniswap"],
    )
    spaces = SnapshotAdapter._extract_spaces(query)
    assert spaces == []


def test_filter_by_terms_matches_title():
    proposals = [
        _proposal(title="Enable WETH collateral", body=""),
        _proposal(id="other", title="Unrelated thing", body="nothing here"),
    ]
    filtered = SnapshotAdapter._filter_by_terms(proposals, ["WETH"])
    assert len(filtered) == 1
    assert filtered[0]["title"] == "Enable WETH collateral"


def test_filter_by_terms_matches_body():
    proposals = [
        _proposal(title="Governance", body="Proposal to adjust AAVE staking rewards"),
    ]
    filtered = SnapshotAdapter._filter_by_terms(proposals, ["staking"])
    assert len(filtered) == 1


def test_filter_by_terms_case_insensitive():
    proposals = [_proposal(title="DeFi Governance Proposal")]
    filtered = SnapshotAdapter._filter_by_terms(proposals, ["defi"])
    assert len(filtered) == 1
