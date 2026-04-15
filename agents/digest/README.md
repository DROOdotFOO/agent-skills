# digest

Multi-platform activity digest agent. Topic in -> synthesized brief out, weighted by engagement signals across 11 sources: Hacker News, GitHub, Reddit, YouTube, ethresear.ch, Snapshot, Polymarket, package registries (hex.pm/crates.io/npm), CoinGecko, Blockscout, and Shodan.

Inspired by [last30days-skill](https://github.com/mvanhorn/last30days-skill).

## Install

```bash
cd agents/digest
pip install -e .
```

Requires `ANTHROPIC_API_KEY` and the `gh` CLI (authenticated) for GitHub search. Optional: `SHODAN_API_KEY` for Shodan adapter.

## Usage

```bash
# Default: HN + GitHub, last 30 days, terminal output
digest generate "rust async runtime"

# Specific window and platforms
digest generate "zero knowledge proofs" --days 7 --platforms hn,github,reddit

# All platforms
digest generate "elixir otp" --platforms hn,github,reddit,youtube,ethresearch,snapshot,polymarket,packages,coingecko,blockscout,shodan

# Write markdown to a file
digest generate "noir language" --output digest.md

# Skip Claude synthesis -- just rank and print raw items
digest generate "elixir otp" --no-synthesis

# List adapters
digest list-platforms

# Watch mode with alerts
digest watch --config digest-watch.example.toml

# Read alerts
digest alerts
```

## Architecture

```
CLI (typer)
  -> Pipeline
       -> Query expansion (static rules, platform-specific terms)
       -> Adapters (11 sources) fetch in parallel
       -> Post-fetch hook (injection pattern scanning)
       -> Dedupe by URL + title similarity
       -> Rank by log-weighted engagement * recency * credibility
       -> Synthesize via Claude (with recall context)
  -> Output (terminal via rich, or markdown file)
```

Each adapter is a small module under `src/digest/adapters/` implementing the `Adapter` protocol (`name: str` + `fetch(query, days, limit) -> list[Item]`).

### Scoring

Three-layer ranking: `log1p(engagement) * weight * (0.7 + 0.3 * recency) * credibility`

Credibility tiers: VERIFIED (1.8x -- Polymarket, Snapshot, Blockscout, on-chain) > DELIBERATE (1.0x -- HN, GitHub, Reddit, ethresearch, Shodan) > PASSIVE (0.5x -- YouTube, packages, CoinGecko). Per-item bonuses (0.0-0.5) from raw data. Historical source accuracy tracking (0.5-1.5x).

## MCP Server

```bash
digest serve
```

7 tools: `digest_generate`, `digest_list_platforms`, `digest_expand_query`, `digest_structured_view`, `digest_recall_context`, `digest_store_to_recall`, `digest_alerts`.

## API Specs

See [SPECS.md](SPECS.md) for planned adapter expansion (17 new sources across research, medical, legal, and security domains).
