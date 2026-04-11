"""Unit tests for CoinGecko adapter item building and term matching."""

from __future__ import annotations

from digest.adapters.coingecko import CoinGeckoAdapter


def _adapter() -> CoinGeckoAdapter:
    return CoinGeckoAdapter()


def test_matches_terms_by_name():
    a = _adapter()
    assert a._matches_terms("Bitcoin", "BTC", ["bitcoin"])
    assert a._matches_terms("Ethereum", "ETH", ["ether"])


def test_matches_terms_by_symbol():
    a = _adapter()
    assert a._matches_terms("Bitcoin", "BTC", ["btc"])
    assert a._matches_terms("Solana", "SOL", ["sol"])


def test_matches_terms_case_insensitive():
    a = _adapter()
    assert a._matches_terms("BITCOIN", "BTC", ["bitcoin"])
    assert a._matches_terms("bitcoin", "btc", ["BTC"])


def test_matches_terms_broad_keywords():
    a = _adapter()
    assert a._matches_terms("Random Token", "RND", ["crypto"])
    assert a._matches_terms("Random Token", "RND", ["defi"])
    assert a._matches_terms("Random Token", "RND", ["token"])


def test_no_match_returns_false():
    a = _adapter()
    assert not a._matches_terms("Bitcoin", "BTC", ["noir"])
    assert not a._matches_terms("Ethereum", "ETH", ["solana"])


def test_empty_terms_matches_everything():
    a = _adapter()
    assert a._matches_terms("Anything", "ANY", [])


def test_adapter_name():
    assert _adapter().name == "coingecko"
