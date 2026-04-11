---
title: Coins Reference
impact: HIGH
impactDescription: Core token price and market data endpoints -- most common queries.
tags: coingecko, prices, market-data, tokens
---

# Coins Reference

## GET /simple/price -- Price by IDs

Query prices for one or more coins by CoinGecko coin ID.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| vs_currencies | string | Yes | Target currency (comma-separated) |
| ids | string | No | Coin IDs (comma-separated). Priority: ids > names > symbols |
| names | string | No | Coin names (URL-encode spaces) |
| symbols | string | No | Coin symbols |
| include_market_cap | boolean | No | Include market cap (default false) |
| include_24hr_vol | boolean | No | Include 24hr volume (default false) |
| include_24hr_change | boolean | No | Include 24hr change % (default false) |
| include_last_updated_at | boolean | No | UNIX timestamp (default false) |
| precision | string | No | Decimal places: full or 0-18 |

At least one of ids, names, or symbols required.

## GET /coins/list -- ID Map

All supported coins with id, symbol, name. No pagination.
Optional `include_platform=true` for contract addresses.
Use this to resolve coin IDs for other endpoints.

## GET /coins/markets -- Market Data List

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| vs_currency | string | Yes | Target currency |
| ids / names / symbols | string | No | Filter (priority: category > ids > names > symbols) |
| category | string | No | Filter by category |
| order | string | No | market_cap_desc (default), volume_desc, id_asc |
| per_page | number | No | 1-250 (default 100) |
| page | number | No | Page number |
| sparkline | boolean | No | 7-day sparkline (default false) |
| price_change_percentage | string | No | Timeframes: 1h,24h,7d,14d,30d,200d,1y |

Returns: current_price, market_cap, market_cap_rank, total_volume, high_24h,
low_24h, price_change_24h, circulating_supply, total_supply, ath, atl.

## GET /coins/{id} -- Full Coin Data

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | CoinGecko coin ID |
| tickers | boolean | No | Exchange tickers (max 100, default true) |
| market_data | boolean | No | Full market data (default true) |
| community_data | boolean | No | Community stats (default true) |
| developer_data | boolean | No | GitHub/repo stats (default true) |
| sparkline | boolean | No | 7-day sparkline (default false) |

Returns: metadata, links, market_data (prices in all currencies, ATH/ATL, supply),
community_data, developer_data, tickers.

## GET /coins/{id}/tickers -- Paginated Tickers

CEX and DEX trading pairs. 100 per page.
Optional: exchange_ids filter, depth (2% order book), trust_score sort.

## GET /coins/top_gainers_losers

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| vs_currency | string | Yes | Target currency |
| duration | string | No | 1h, 24h (default), 7d, 14d, 30d, 60d, 1y |
| top_coins | string | No | Market cap filter: 300, 500, 1000 (default), all |

Returns 30 top_gainers + 30 top_losers. Min $50k 24hr volume.

## GET /coins/list/new

Recently listed coins with activation timestamps. No parameters.
