---
title: Contract Address Reference
impact: MEDIUM
impactDescription: Look up token data by contract address instead of CoinGecko coin ID.
tags: coingecko, contract, token, address
---

# Contract Address Reference

Query token data using contract addresses instead of CoinGecko IDs. Useful when
you have a token address from on-chain activity.

## GET /simple/token_price/{platform_id}

Current price by contract address.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| platform_id | string | Yes | Asset platform (e.g. ethereum, polygon-pos, base) |
| contract_addresses | string | Yes | Comma-separated token addresses |
| vs_currencies | string | Yes | Target currencies |
| include_market_cap | boolean | No | Default false |
| include_24hr_vol | boolean | No | Default false |
| include_24hr_change | boolean | No | Default false |

## GET /coins/{platform_id}/contract/{contract_address}

Full coin metadata + market data by contract. Same response as GET /coins/{id}.

## GET /coins/{platform_id}/contract/{contract_address}/market_chart

Historical price, market cap, volume time-series.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| vs_currency | string | Yes | Target currency |
| days | string | Yes | Lookback: 1, 7, 14, 30, 90, 180, 365, max |
| interval | string | No | daily, hourly (auto if omitted) |
| precision | string | No | Decimal places |

Returns arrays of [timestamp, value] pairs.

## GET /coins/{platform_id}/contract/{contract_address}/market_chart/range

Same as above but with explicit from/to UNIX timestamps.

## Common platform IDs

| Platform | ID | Notes |
|----------|----|-------|
| Ethereum | ethereum | ERC-20 tokens |
| Polygon PoS | polygon-pos | |
| Arbitrum One | arbitrum-one | |
| Optimism | optimistic-ethereum | |
| Base | base | |
| Avalanche | avalanche-2 | C-Chain |
| BSC | binance-smart-chain | BEP-20 tokens |
| Solana | solana | SPL tokens (use mint address) |
| Tron | tron | TRC-20 tokens (use TRC-20 contract address) |
| Near | near-protocol | |
| Fantom | fantom | |
| zkSync Era | zksync | |

### Solana example

```bash
# SPL token price by mint address
GET /simple/token_price/solana?contract_addresses=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v&vs_currencies=usd

# Token metadata by contract
GET /coins/solana/contract/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
```

### Tron example

```bash
# TRC-20 token price by contract address
GET /simple/token_price/tron?contract_addresses=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t&vs_currencies=usd

# Token metadata by contract
GET /coins/tron/contract/TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t
```
