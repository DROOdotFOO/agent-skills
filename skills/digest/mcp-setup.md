---
impact: MEDIUM
impactDescription: "MCP server configuration, tool list, and install instructions"
tags: "digest,mcp,setup,install"
---

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
| `digest_structured_view` | Generate digest with structured view (timeline, controversy, tags, sources) |
| `digest_recall_context` | Fetch historical context from recall knowledge base |
| `digest_store_to_recall` | Store top digest items to recall for future reference |
| `digest_alerts` | Read recent alerts from the digest watch system |

## Install

```bash
cd agents/digest
pip install -e .
```

Requires `ANTHROPIC_API_KEY` and the `gh` CLI (authenticated) for GitHub search.
