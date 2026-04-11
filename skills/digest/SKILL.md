---
name: digest
description: >
  Generate a multi-platform activity digest for a topic. Fetches and ranks
  items from HN, GitHub, Reddit, YouTube, ethresear.ch, Snapshot, Polymarket,
  and package registries. TRIGGER when: user invokes "/digest" or asks for
  a "digest", "what's happening with X", "activity summary for X", "news about X".
  DO NOT TRIGGER when: user asks about digest agent code/implementation.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: digest, research, monitoring, news
---

# Digest

Generate a synthesized activity digest for any topic across multiple platforms.

## Usage

```bash
# Default: HN + GitHub, last 30 days, terminal output
digest generate "rust async runtime"

# Narrow time window, specific platforms
digest generate "zero knowledge proofs" --days 7 --platforms hn,github,reddit

# Write markdown to file
digest generate "noir language" --output digest.md

# Skip Claude synthesis -- just rank and print raw items
digest generate "elixir otp" --no-synthesis

# Skip query expansion -- search the topic string literally
digest generate "noir" --no-expansion

# List available platform adapters
digest list-platforms
```

## Available Platforms

| Platform | Adapter key | Signal source |
|----------|-------------|---------------|
| Hacker News | `hn` | Algolia search API (points, comments) |
| GitHub | `github` | `gh` CLI search (stars, forks, recent activity) |
| Reddit | `reddit` | Reddit search JSON API (upvotes, comments) |
| YouTube | `youtube` | yt-dlp flat-playlist search (views, likes) |
| ethresear.ch | `ethresearch` | Discourse search (views, likes, posts) |
| Snapshot | `snapshot` | GraphQL governance API (votes, scores) |
| Polymarket | `polymarket` | Gamma API market data (volume traded) |
| Package registries | `packages` | hex.pm + crates.io + npm (recent downloads) |
| CoinGecko | `coingecko` | Trending tokens, top gainers/losers, new listings |
| Blockscout | `blockscout` | On-chain token transfers and address activity (Ethereum) |

## Flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--days` | `-d` | 30 | Lookback window in days |
| `--platforms` | `-p` | `hn,github` | Comma-separated platform list |
| `--max-items` | `-n` | 50 | Max items fetched per platform |
| `--output` | `-o` | (none) | Write markdown to file instead of terminal |
| `--no-synthesis` | | false | Skip Claude narrative synthesis |
| `--no-expansion` | | false | Skip query expansion, search literally |

## Query Expansion

The digest agent auto-expands known topics into structured queries with
platform-specific hints. For example, searching "noir" expands into compound
phrases for HN (to avoid film noir / wine matches), GitHub org qualifiers
(`org:noir-lang`), and topic tags.

Expansion produces:
- **terms** -- generic full-text search terms
- **hn_terms** -- HN-specific compound phrases (avoids ambiguous short words)
- **github_qualifiers** -- org/repo scoping (e.g. `org:noir-lang`, `repo:tokio-rs/tokio`)
- **github_topics** -- topic tag filters

If no expansion rules match, the topic is searched literally. Use `--no-expansion`
to force literal search even when rules exist.

## Pipeline

1. Query expansion (static rules, LLM fallback planned)
2. Parallel fetch across selected adapters
3. Dedupe by URL + title similarity
4. Rank by log-weighted engagement + recency decay
5. Synthesize narrative via Claude (unless `--no-synthesis`)
6. Output to terminal (rich) or markdown file

## MCP Server

Start the MCP server (stdio transport):

```bash
digest serve
```

### Configure MCP

Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "digest": {
      "command": "digest",
      "args": ["serve"]
    }
  }
}
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `digest_generate` | Generate a synthesized digest for a topic across platforms |
| `digest_list_platforms` | List available platform adapters |
| `digest_expand_query` | Preview query expansion for a topic |

## Install

```bash
cd agents/digest
pip install -e .
```

Requires `ANTHROPIC_API_KEY` and the `gh` CLI (authenticated) for GitHub search.
