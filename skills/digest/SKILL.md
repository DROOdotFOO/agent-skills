---
name: digest
description: >
  Generate a multi-platform activity digest for a topic. Fetches and ranks
  items from HN, GitHub, Reddit, YouTube, ethresear.ch, Snapshot, Polymarket,
  package registries, CoinGecko, Blockscout, and Shodan. TRIGGER when: user
  invokes "/digest" or asks for a "digest", "what's happening with X",
  "activity summary for X", "news about X".
  DO NOT TRIGGER when: user asks about digest agent code/implementation.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: digest, research, monitoring, news
  argument-hint: '"<topic>" [--days N] [--platforms p1,p2]'
---

# Digest

Generate a synthesized activity digest for any topic across multiple platforms.

## What You Get

- Ranked list of items across platforms, weighted by engagement and recency
- Claude-synthesized narrative with citations (or raw items with `--no-synthesis`)
- Markdown file or terminal output

## Usage

```bash
digest generate "rust async runtime"
digest generate "zero knowledge proofs" --days 7 --platforms hn,github,reddit
digest generate "noir language" --output digest.md
digest generate "elixir otp" --no-synthesis
digest generate "noir" --no-expansion
digest list-platforms
```

## Available Platforms

| Platform | Key | Signal source |
|----------|-----|---------------|
| Hacker News | `hn` | Algolia search (points, comments) |
| GitHub | `github` | `gh` CLI search (stars, forks) |
| Reddit | `reddit` | Search JSON API (upvotes, comments) |
| YouTube | `youtube` | yt-dlp flat-playlist (views, likes) |
| ethresear.ch | `ethresearch` | Discourse search (views, likes, posts) |
| Snapshot | `snapshot` | GraphQL governance (votes, scores) |
| Polymarket | `polymarket` | Gamma API (volume traded) |
| Packages | `packages` | hex.pm + crates.io + npm (downloads) |
| CoinGecko | `coingecko` | Trending, gainers/losers, new listings |
| Blockscout | `blockscout` | On-chain transfers, address activity |
| Shodan | `shodan` | Hosts, services, CVEs (SHODAN_API_KEY) |

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--days` / `-d` | 30 | Lookback window in days |
| `--platforms` / `-p` | `hn,github` | Comma-separated platform list |
| `--max-items` / `-n` | 50 | Max items per platform |
| `--output` / `-o` | (none) | Write markdown to file |
| `--no-synthesis` | false | Skip Claude narrative |
| `--no-expansion` | false | Skip query expansion |

## Pipeline

1. Query expansion (static rules, LLM fallback planned)
2. Parallel fetch across selected adapters
3. Dedupe by URL + title similarity
4. Rank by log-weighted engagement + recency decay
5. Synthesize narrative via Claude (unless `--no-synthesis`)
6. Output to terminal (rich) or markdown file

## Reference

| File | Topic |
|------|-------|
| [mcp-setup.md](mcp-setup.md) | MCP server config and tool list |
