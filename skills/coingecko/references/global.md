---
title: Global Market Data Reference
impact: MEDIUM
impactDescription: Global crypto market statistics and DeFi aggregate metrics.
tags: coingecko, global, market-cap, defi
---

# Global Market Data Reference

## GET /global

Global crypto market stats. No parameters.

Key response fields:
- active_cryptocurrencies: total tracked coins
- total_market_cap: by currency (usd, btc, eth, etc.)
- total_volume: 24hr volume by currency
- market_cap_percentage: dominance (btc, eth, usdt, etc.)
- market_cap_change_percentage_24h_usd
- updated_at: UNIX timestamp

## GET /global/decentralized_finance_defi

Top 100 DeFi coins aggregated. No parameters.

Key response fields:
- defi_market_cap: total DeFi market cap (string)
- eth_market_cap: Ethereum market cap (string)
- defi_to_eth_ratio: DeFi/ETH ratio (string)
- trading_volume_24h: 24hr DeFi volume (string)
- defi_dominance: DeFi dominance % (string)
- top_coin_name / top_coin_defi_dominance

## GET /global/market_cap_chart

Historical global market cap + volume time-series.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| days | string | Yes | 1, 7, 14, 30, 90, 180, 365, or max |
| vs_currency | string | No | Default: usd |

Granularity: 1d = hourly, 2d+ = daily.
Returns arrays of [timestamp, value] pairs for market_cap and volume.
