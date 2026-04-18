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

## Reference

| File | Topic |
|------|-------|
| [cheat-sheet.md](cheat-sheet.md) | Key endpoints, conventions, error codes |
| [mcp-setup.md](mcp-setup.md) | MCP server config (remote + local) |
| [references/coins.md](references/coins.md) | Token prices, market cap, coin lookup |
| [references/onchain-pools.md](references/onchain-pools.md) | DEX pools, trending, megafilter |
| [references/contract.md](references/contract.md) | Price by contract address |
| [references/global.md](references/global.md) | Global market stats, DeFi metrics |

## What You Get

- Reference documentation for CoinGecko and GeckoTerminal API endpoints covering token prices, market data, DEX pools, and on-chain analytics.
- Guidance on when to use aggregated CoinGecko data vs pool-level GeckoTerminal data, with multi-chain platform IDs.
- Authentication tiers, rate limits, and MCP server configuration for automated queries.

## See also

- `blockscout` -- on-chain contract state, transactions, token transfers
- `ethskills` -- Ethereum tooling, framework selection, EIP/ERC standards
- `sentinel` -- on-chain contract monitoring and anomaly detection
