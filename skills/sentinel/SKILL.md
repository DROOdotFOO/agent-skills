---
name: sentinel
description: >
  Monitor on-chain contracts for anomalous transactions. Checks for large transfers,
  ownership changes, unusual methods, and selfdestruct calls via Blockscout API v2.
  TRIGGER when: user asks about contract monitoring, "check this contract",
  on-chain alerts, "any suspicious transactions", or invokes "/sentinel".
  DO NOT TRIGGER when: user is working on sentinel agent code itself.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: sentinel, blockchain, monitoring, security, web3
---

# Sentinel

On-chain contract monitor. 4 alert rules (large transfers, ownership changes,
unusual methods, selfdestruct) across 8 chains via Blockscout API v2.

## What You Get

- Alert list: large transfers, ownership changes, unusual methods, selfdestruct calls
- JSONL alert log at `~/.local/share/sentinel/alerts.jsonl`
- macOS notifications for continuous watch mode

## CLI Usage

```bash
# One-shot contract check
sentinel check --address 0x... --chain 1

# Check from a specific block
sentinel check --address 0x... --chain 8453 --since-block 12345678

# Continuous monitoring from config
sentinel watch --config sentinel.toml

# View recent alerts
sentinel alerts --limit 20
```

## Supported Chains

EVM-only. Not available for native Solana or Tron -- use coingecko skill for
token data on those chains.

| Chain | ID | Chain | ID |
|-------|----|-------|----|
| Ethereum | 1 | Arbitrum One | 42161 |
| Polygon | 137 | OP Mainnet | 10 |
| Base | 8453 | zkSync Era | 324 |
| Gnosis | 100 | Scroll | 534352 |
| Celo | 42220 | Mode | 34443 |
| Neon EVM (Solana) | 245022934 | | |

## MCP Server

```bash
sentinel serve
```

### Configure MCP

Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "sentinel": {
      "command": "sentinel",
      "args": ["serve"]
    }
  }
}
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `sentinel_check` | Check a contract for anomalous transactions |
| `sentinel_alerts` | Show recent alerts from the local log |

## Install

```bash
cd agents/sentinel
pip install -e .
```

No API keys required -- uses public Blockscout API v2 endpoints.
