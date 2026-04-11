---
name: autoresearch
description: >
  Check and run autonomous experiments. Query experiment status, view results
  dashboards, and execute iterations.
  TRIGGER when: user asks about experiment status, autoresearch progress,
  "how's the experiment going", "run another iteration", or invokes "/autoresearch".
  DO NOT TRIGGER when: user is working on autoresearch agent code itself.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: autoresearch, experiments, optimization, agents
---

# Autoresearch

Domain-agnostic autonomous experiment runner. Optimizes a single metric by
iterating: hypothesis -> code change -> verify -> keep/discard.

## CLI Usage

```bash
# Initialize an experiment
autoresearch init noir-gates \
  --objective "minimize constraint count" \
  --metric constraints \
  --verify "nargo compile 2>&1 | grep constraints" \
  --direction lower \
  --mutable src/main.nr

# Run a single iteration
autoresearch run "inline witness computation"

# Autonomous loop (Claude generates hypotheses)
autoresearch loop --iterations 10 --model claude-sonnet-4-6

# View results
autoresearch dashboard
autoresearch status
```

## MCP Server

```bash
autoresearch serve
```

### Configure MCP

Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "autoresearch": {
      "command": "autoresearch",
      "args": ["serve"]
    }
  }
}
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `autoresearch_status` | Current experiment status (name, metric, runs, best) |
| `autoresearch_dashboard` | Full results table as markdown |
| `autoresearch_run` | Execute a single experiment iteration |

## Install

```bash
cd agents/autoresearch
pip install -e .
```

Requires `ANTHROPIC_API_KEY` for the autonomous loop (hypothesis generation).
