---
name: coingecko
description: >
  CoinGecko and GeckoTerminal API reference for crypto market data, token prices,
  DEX pools, and on-chain analytics.
  TRIGGER when: user asks about token/coin prices, market caps, trading volume,
  DEX pools, trending tokens, price history, crypto market data, or CoinGecko API usage.
  DO NOT TRIGGER when: user asks about on-chain contract state or transactions
  (use blockscout skill), or Solidity/smart contract code (use solidity-audit skill).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: coingecko, crypto, prices, defi, dex, market-data, web3
---

# CoinGecko

Crypto market data via CoinGecko (aggregated CEX+DEX) and GeckoTerminal (on-chain DEX).

## Strict rule

Never answer questions about crypto prices, market caps, volumes, supply, TVL,
exchange rates, or any time-sensitive market data using training knowledge.
Only live API responses provide accurate figures.

## When to use which API

**CoinGecko** (aggregated): Established tokens, broad market analysis, cross-exchange
prices. Covers thousands of reviewed coins with volume-weighted aggregation.

**GeckoTerminal** (on-chain DEX): Pool-level data, newly launched tokens not yet on
CoinGecko, on-chain trade history, DEX-specific queries. Covers millions of unreviewed
tokens.

Prefer CoinGecko when both could answer -- aggregated data is broader and less
susceptible to thin-liquidity distortion.

**Multi-chain**: CoinGecko covers tokens across all major chains including Ethereum,
Solana (SPL tokens by mint address), Tron (TRC-20 by contract), Polygon, Base,
Arbitrum, BSC, Avalanche, and 100+ more platforms. Use contract endpoints with
the appropriate platform ID (e.g. `solana`, `tron`, `ethereum`).

## Authentication

| Plan | Base URL | Rate limit | Auth header |
|------|----------|------------|-------------|
| Pro | `https://pro-api.coingecko.com/api/v3` | 250+ calls/min | `x-cg-pro-api-key: KEY` |
| Demo | `https://api.coingecko.com/api/v3` | 30 calls/min | `x-cg-demo-api-key: KEY` |
| Keyless | `https://api.coingecko.com/api/v3` | 5 calls/min | (none) |

GeckoTerminal endpoints use `/onchain` prefix on the same base URLs.

## MCP Server

CoinGecko provides an official MCP server for live data access. Two options:

### Option 1: Remote (no install, keyless)

Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "coingecko": {
      "url": "https://mcp.api.coingecko.com/mcp"
    }
  }
}
```

Rate limited but works without API keys.

### Option 2: Local stdio (higher limits)

```json
{
  "mcpServers": {
    "coingecko": {
      "command": "npx",
      "args": ["-y", "@coingecko/coingecko-mcp"],
      "env": {
        "COINGECKO_DEMO_API_KEY": "your-free-demo-key"
      }
    }
  }
}
```

Get a free Demo key at coingecko.com/en/api (30 calls/min).

### MCP tools

The server exposes 76+ API endpoints as tools including coin prices, market data,
trending tokens, DEX pools, NFTs, and historical charts. It uses a code execution
sandbox -- you write TypeScript against the CoinGecko SDK.

## Reading guide

| Question | Read |
|----------|------|
| Token prices, market cap, coin lookup | [coins](references/coins.md) |
| DEX pools, trending, megafilter | [onchain-pools](references/onchain-pools.md) |
| Price by contract address | [contract](references/contract.md) |
| Global market stats, DeFi metrics | [global](references/global.md) |

## Key endpoints cheat sheet

```bash
# Current price
GET /simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true

# Market data with ranking
GET /coins/markets?vs_currency=usd&per_page=50&sparkline=true

# Coin metadata + market data
GET /coins/{id}?tickers=false&community_data=false

# Price by contract address
GET /simple/token_price/{platform_id}?contract_addresses=0x...&vs_currencies=usd

# Top gainers/losers
GET /coins/top_gainers_losers?vs_currency=usd&duration=24h

# Trending DEX pools
GET /onchain/networks/trending_pools?duration=24h

# Pool megafilter
GET /onchain/pools/megafilter?networks=eth&sort=h24_volume_usd_desc&reserve_in_usd_min=100000

# Global market cap
GET /global
```

## Common conventions

- **Coin ID resolution**: Use `GET /coins/list` or `GET /search` to map symbols to IDs
- **Auto-granularity for charts**: 1d = 5-min, 2-90d = hourly, 90d+ = daily (00:00 UTC)
- **Date formats**: ISO `YYYY-MM-DD` for most endpoints, `DD-MM-YYYY` for `/coins/{id}/history`
- **Latest daily data**: Available 10-35 min after midnight UTC

## Error handling

| Code | Meaning |
|------|---------|
| 401 | No API key |
| 429 | Rate limit exceeded |
| 10002 | Wrong auth method |
| 10005 | Endpoint requires higher tier |
| 10010 | Pro key on Demo URL (or vice versa) |

## See also

- `blockscout` -- on-chain contract state, transactions, token transfers
- `ethskills` -- Ethereum tooling, framework selection, EIP/ERC standards
- `sentinel` -- on-chain contract monitoring and anomaly detection
