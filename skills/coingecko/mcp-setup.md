---
impact: MEDIUM
impactDescription: "MCP server configuration for remote and local CoinGecko access"
tags: "coingecko,mcp,setup"
---

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
