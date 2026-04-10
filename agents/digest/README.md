# digest

Multi-platform activity digest agent. Topic in -> synthesized brief out, weighted by engagement signals across Hacker News, GitHub, and (soon) Reddit, X, YouTube.

Inspired by [last30days-skill](https://github.com/mvanhorn/last30days-skill).

## Install

```bash
cd agents/digest
pip install -e .
```

Requires `ANTHROPIC_API_KEY` and the `gh` CLI (authenticated) for GitHub search.

## Usage

```bash
# Default: HN + GitHub, last 30 days, terminal output
digest generate "rust async runtime"

# Specific window and platforms
digest generate "zero knowledge proofs" --days 7 --platforms hn,github

# Write markdown to a file
digest generate "noir language" --output digest.md

# List adapters
digest list-platforms
```

## Architecture

```
CLI (typer)
  -> Pipeline
       -> Adapters (HN, GitHub, ...) fetch in parallel
       -> dedupe by URL + title similarity
       -> rank by log-weighted engagement + recency
       -> synthesize via Claude Opus 4.6 (adaptive thinking)
  -> Output (terminal via rich, or markdown file)
```

Each adapter is a small module under `src/digest/adapters/` implementing the `Adapter` protocol (name + `fetch(topic, days, limit) -> list[Item]`).

## Status

Phase 1 MVP: HN + GitHub adapters, engagement ranking, Claude synthesis, markdown/terminal output.

Coming in Phase 2 (see repo `TODO.md`):
- Reddit (oauth), X, YouTube (yt-dlp), Farcaster, Snapshot, Blockscout
- Differential mode (what changed since last digest)
- Feed memory (sqlite) for trend queries
- MCP server mode
