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
  argument-hint: '"<query>" [--project p] [--type t]'
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

# List, get, delete, stats
recall list --project recall --limit 10
recall get 1
recall delete 1
recall stale --days 90
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

## When to Use

- Before making architectural decisions, search for prior decisions on the topic
- After resolving a tricky bug, store the gotcha for future reference
- When encountering a useful pattern, capture it with project and tags
- When finding a valuable resource, save it as a link entry

## What You Get

- Full CLI and MCP tool reference for querying and storing knowledge entries (decisions, patterns, gotchas, links, insights)
- Entry type guidance so you store knowledge in the right category for later retrieval
- Search and filtering patterns for finding relevant past context by project, type, or full-text query

## Reference

| File | Topic |
|------|-------|
| [mcp-setup.md](mcp-setup.md) | MCP server config, tools, storage, install |
