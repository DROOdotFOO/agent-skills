---
name: recall
description: >
  Query the recall knowledge base for relevant context. Searches decisions,
  patterns, gotchas, links, and insights stored across sessions.
  TRIGGER when: user asks to "recall", "remember", "what did we decide about",
  "check knowledge base", or references past decisions/patterns.
  DO NOT TRIGGER when: user is talking about memory/recall in a general sense,
  or working on the recall agent code itself.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: recall, knowledge, context, memory
---

# Recall

Query and store knowledge entries (decisions, patterns, gotchas, links, insights)
in a local SQLite database with full-text search.

## CLI Usage

```bash
# Add entries
recall add "Always quote FTS5 tokens containing hyphens" --type gotcha --project recall --tags sqlite,fts5
recall add "Use WAL mode for concurrent reads" --type pattern --project myproj

# Search (full-text, with optional filters)
recall search "sqlite"
recall search "architecture" --project myproj --type decision

# List recent entries
recall list --project recall --limit 10

# Get / delete by ID
recall get 1
recall delete 1

# Find stale entries (not accessed recently)
recall stale --days 90

# Store statistics
recall stats
```

## Entry Types

| Type       | Use for                                          |
| ---------- | ------------------------------------------------ |
| `decision` | Architectural or design decisions with rationale |
| `pattern`  | Reusable approaches or techniques                |
| `gotcha`   | Non-obvious pitfalls or footguns                 |
| `link`     | External resources worth remembering             |
| `insight`  | General observations or learnings (default)      |

## MCP Server

Start the MCP server (stdio transport):

```bash
recall serve
```

### Configure MCP

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

| Tool            | Description                                         |
| --------------- | --------------------------------------------------- |
| `recall_search` | Full-text search with filters (project, type, tags) |
| `recall_add`    | Add a knowledge entry                               |
| `recall_list`   | List recent entries                                 |
| `recall_get`    | Get a single entry by ID                            |
| `recall_delete` | Delete an entry                                     |
| `recall_stats`  | Store statistics                                    |
| `recall_stale`  | Find entries not accessed recently                  |

## Storage

SQLite database at `~/.local/share/recall/recall.db` (WAL mode, FTS5 with porter
stemming). Override location with `--db <path>`.

## Install

```bash
cd agents/recall
pip install -e ".[dev]"
```

## When to Use

- Before making architectural decisions, search for prior decisions on the topic
- After resolving a tricky bug, store the gotcha for future reference
- When encountering a useful pattern, capture it with project and tags
- When finding a valuable resource, save it as a link entry
