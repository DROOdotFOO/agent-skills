---
title: On-Chain Pools Reference
impact: HIGH
impactDescription: DEX pool discovery, trending tokens, and advanced filtering via GeckoTerminal.
tags: coingecko, geckoterminal, dex, pools, defi, onchain
---

# On-Chain Pools Reference (GeckoTerminal)

All endpoints use `/onchain` prefix. Pool data includes address, name, prices,
FDV, reserves, price changes (5m to 24h), transaction counts, and volume.

Common network IDs: `eth`, `solana`, `tron`, `polygon_pos`, `arbitrum`, `base`,
`optimism`, `bsc`, `avalanche`, `fantom`. Use `GET /onchain/networks` for full list.

## Key pool attributes

- price_change_percentage: m5, m15, m30, h1, h6, h24
- transactions: buys, sells, buyers, sellers per interval
- volume_usd: per interval
- reserve_in_usd: total liquidity
- fdv_usd / market_cap_usd (null if unverified)

## Endpoints

### GET /onchain/networks/{network}/pools/{address}

Single pool lookup with extended attributes (composition, volume breakdown).

### GET /onchain/networks/{network}/pools/multi/{addresses}

Batch lookup up to 50 pools. Same extended attributes.

### GET /onchain/networks/trending_pools

Trending pools across all networks.
Optional: duration (5m, 1h, 6h, 24h), include_gt_community_data.

### GET /onchain/networks/{network}/trending_pools

Trending pools on a specific network.

### GET /onchain/networks/{network}/pools

Top pools by network. Sort: h24_tx_count_desc (default), h24_volume_usd_desc.

### GET /onchain/networks/{network}/dexes/{dex}/pools

Top pools for a specific DEX on a network.

### GET /onchain/networks/new_pools

New pools from past 48 hours across all networks.

### GET /onchain/pools/megafilter

Advanced filtering across networks. Key filters:

| Filter | Description |
|--------|-------------|
| networks / dexes | Scope by network and DEX |
| fdv_usd_min/max | FDV range |
| reserve_in_usd_min/max | Liquidity range |
| h24_volume_usd_min/max | Volume range |
| pool_created_hour_min/max | Pool age in hours |
| tx_count_min/max | Transaction count range |
| price_change_percentage_min/max | Price change range |
| checks | no_honeypot, good_gt_score, on_coingecko, has_social |

Sort options: trending (m5/h1/h6/h24), tx_count, volume, fdv, reserve, price,
pool_created_at.

### GET /onchain/search/pools

Search by pool address, token name/symbol, or token contract address.
Optional: network filter.
