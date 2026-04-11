---
title: OpenAPI-to-MCP Scaffolding
impact: CRITICAL
impactDescription: Core conversion logic from OpenAPI specs to MCP tool definitions
tags: mcp, openapi, fastmcp, typescript, scaffolding, schema-mapping
---

# OpenAPI-to-MCP Scaffolding

## Path-to-Tool Mapping

Each OpenAPI path + HTTP method becomes one MCP tool:

| OpenAPI | MCP Tool |
| --- | --- |
| `GET /repos/{owner}/{repo}` | `get_repo` |
| `POST /repos/{owner}/{repo}/issues` | `create_issue` |
| `DELETE /repos/{owner}/{repo}` | `delete_repo` |
| `PUT /users/{id}/roles` | `update_user_roles` |
| `PATCH /orgs/{org}/settings` | `update_org_settings` |

### Naming Conventions

- Format: `verb_noun` in `snake_case`
- HTTP method mapping: GET -> `get_`/`list_`, POST -> `create_`, PUT/PATCH -> `update_`, DELETE -> `delete_`
- Use `list_` for endpoints returning arrays, `get_` for single resources
- Prefix with API name when building multi-API servers: `github_list_repos`, `stripe_create_charge`
- Avoid generic names: `get_data`, `do_action`, `handle_request`

### Parameter Mapping

OpenAPI parameters map to MCP tool `inputSchema` properties:

```
OpenAPI location  ->  MCP inputSchema
-----------------     ----------------
path parameters   ->  required properties
query parameters  ->  optional properties (unless OpenAPI marks required)
request body      ->  flattened into properties (or nested if complex)
headers           ->  omit from schema; handle in auth layer
```

For request bodies with deeply nested schemas, flatten to two levels max.
Extract reusable `$ref` schemas into shared definitions.

## Python (FastMCP) Scaffold

```python
"""MCP server for <API_NAME>."""

import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("<api_name>")

API_BASE = os.environ["API_NAME_BASE_URL"]
API_KEY = os.environ["API_NAME_API_KEY"]

ALLOWED_HOSTS = ["api.example.com"]


def _client() -> httpx.Client:
    """Create authenticated HTTP client."""
    return httpx.Client(
        base_url=API_BASE,
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=30.0,
    )


def _check_host(url: str) -> None:
    """Validate request target against allowlist."""
    from urllib.parse import urlparse
    host = urlparse(url).hostname
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"Host {host} not in allowlist: {ALLOWED_HOSTS}")


@mcp.tool()
def list_items(page: int = 1, per_page: int = 20) -> dict:
    """List all items with pagination.

    Args:
        page: Page number (default: 1).
        per_page: Items per page (default: 20, max: 100).
    """
    with _client() as client:
        resp = client.get("/items", params={"page": page, "per_page": per_page})
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def get_item(item_id: str) -> dict:
    """Get a single item by ID.

    Args:
        item_id: The unique item identifier.
    """
    with _client() as client:
        resp = client.get(f"/items/{item_id}")
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def delete_item(item_id: str, confirm: bool = False) -> dict:
    """Delete an item. Requires explicit confirmation.

    Args:
        item_id: The unique item identifier.
        confirm: Must be True to proceed with deletion.
    """
    if not confirm:
        return {"error": "Set confirm=True to delete this item", "code": 400}
    with _client() as client:
        resp = client.delete(f"/items/{item_id}")
        resp.raise_for_status()
        return {"deleted": item_id}
```

### Running the Python server

```bash
# stdio transport (default for Claude Code)
python -m mcp_server

# SSE transport (for remote/shared access)
mcp run --transport sse --port 8080
```

## TypeScript Scaffold

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const API_BASE = process.env.API_NAME_BASE_URL!;
const API_KEY = process.env.API_NAME_API_KEY!;
const ALLOWED_HOSTS = ["api.example.com"];

function checkHost(url: string): void {
  const host = new URL(url).hostname;
  if (!ALLOWED_HOSTS.includes(host)) {
    throw new Error(`Host ${host} not in allowlist: ${ALLOWED_HOSTS}`);
  }
}

async function apiRequest(path: string, options: RequestInit = {}): Promise<unknown> {
  const url = `${API_BASE}${path}`;
  checkHost(url);
  const resp = await fetch(url, {
    ...options,
    headers: {
      Authorization: `Bearer ${API_KEY}`,
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!resp.ok) {
    return { error: resp.statusText, code: resp.status };
  }
  return resp.json();
}

const server = new McpServer({ name: "api_name", version: "1.0.0" });

server.tool(
  "list_items",
  "List all items with pagination",
  {
    page: z.number().default(1).describe("Page number"),
    per_page: z.number().default(20).describe("Items per page (max 100)"),
  },
  async ({ page, per_page }) => {
    const data = await apiRequest(`/items?page=${page}&per_page=${per_page}`);
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

server.tool(
  "delete_item",
  "Delete an item (requires confirmation)",
  {
    item_id: z.string().describe("Unique item identifier"),
    confirm: z.boolean().default(false).describe("Must be true to proceed"),
  },
  async ({ item_id, confirm }) => {
    if (!confirm) {
      return {
        content: [{ type: "text", text: JSON.stringify({ error: "Set confirm=true", code: 400 }) }],
      };
    }
    const data = await apiRequest(`/items/${item_id}`, { method: "DELETE" });
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Schema Generation Tips

- Use the OpenAPI `description` field directly as the MCP tool description
- If the OpenAPI description is missing or too terse, write one that explains
  what the tool does and when to use it (LLMs rely on descriptions for routing)
- Map `enum` values to zod `.enum()` (TS) or `Literal` union (Python)
- Map `format: date-time` to string with description noting ISO 8601
- For `oneOf`/`anyOf`, pick the most common variant or use a union type
- Default pagination to sensible limits (20 items) even if the API allows more
