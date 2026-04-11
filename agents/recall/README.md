# recall

Knowledge capture and retrieval agent. Stores decisions, patterns, gotchas, links, and insights in a local SQLite database with FTS5 full-text search. Exposes both a CLI and an MCP server for Claude Code integration.

Inspired by [paperclip](https://github.com/paperclipai/paperclip).

## Status: MVP

## Install

```bash
cd agents/recall
pip install -e ".[dev]"
```

## CLI

```bash
recall add "Always quote FTS5 tokens containing hyphens" --type gotcha --project recall --tags sqlite,fts5
recall search "sqlite"
recall search "architecture" --project myproj --type decision
recall list --project recall --limit 10
recall get 1
recall delete 1
recall stale --days 90
recall stats
```

### Entry types

| Type | Use for |
|------|---------|
| `decision` | Architectural or design decisions with rationale |
| `pattern` | Reusable approaches or techniques |
| `gotcha` | Non-obvious pitfalls or footguns |
| `link` | External resources worth remembering |
| `insight` | General observations or learnings (default) |

## MCP Server

Start the MCP server (stdio transport):

```bash
recall serve
```

Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "recall": {
      "command": "recall",
      "args": ["serve"]
    }
  }
}
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `recall_add` | Add a knowledge entry |
| `recall_search` | Full-text search with filters (project, type, tags) |
| `recall_list` | List recent entries |
| `recall_get` | Get a single entry by ID |
| `recall_delete` | Delete an entry |
| `recall_stats` | Store statistics |
| `recall_stale` | Find entries not accessed recently |

## Storage

SQLite database at `~/.local/share/recall/recall.db` (WAL mode, FTS5 with porter stemming). Override with `--db <path>`.

## Tests

```bash
cd agents/recall
python -m pytest tests/ -v
```
