---
impact: MEDIUM
impactDescription: "MCP server configuration, tool list, storage details, and install instructions"
tags: "recall,mcp,setup,storage"
---

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
