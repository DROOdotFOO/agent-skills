---
title: Auth and Safety Patterns
impact: CRITICAL
impactDescription: Security design for MCP servers -- secrets, allowlists, error handling, destructive action gates
tags: mcp, security, auth, secrets, error-handling, rate-limiting
---

# Auth and Safety Patterns

## Secrets Management

**Rule: secrets live in environment variables only.**

Never put API keys, tokens, or credentials in:
- MCP tool `inputSchema` defaults
- Tool descriptions
- Hardcoded strings in server code
- Configuration files checked into version control

### Correct pattern

```python
import os

API_KEY = os.environ["SERVICE_API_KEY"]  # fails fast if missing
```

```typescript
const API_KEY = process.env.SERVICE_API_KEY;
if (!API_KEY) throw new Error("SERVICE_API_KEY not set");
```

### Env var naming convention

```
<SERVICE>_API_KEY       # primary auth token
<SERVICE>_BASE_URL      # API base URL
<SERVICE>_WEBHOOK_SECRET # webhook signature key
```

### Integration with 1Password (recommended for this setup)

```bash
# In MCP server config (mcp.json / claude_desktop_config.json)
{
  "env": {
    "SERVICE_API_KEY": { "op": "op://Vault/Item/field" }
  }
}
```

Or at runtime:

```bash
export SERVICE_API_KEY=$(op read "op://Vault/Item/credential")
```

## Host Allowlists

Every MCP server that makes HTTP requests must enforce a host allowlist.
This prevents prompt injection attacks from redirecting requests to
attacker-controlled servers.

```python
ALLOWED_HOSTS = ["api.github.com", "api.stripe.com"]

def validate_host(url: str) -> None:
    from urllib.parse import urlparse
    host = urlparse(url).hostname
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"Blocked request to {host}")
```

### Rules

- No wildcard entries (`*.example.com`) unless the API genuinely uses
  dynamic subdomains (e.g., `<tenant>.api.example.com`)
- Include only production API hosts, not CDNs or docs sites
- Log blocked requests for debugging

## Destructive Action Confirmation

Any tool that performs a destructive operation (DELETE, DROP, PURGE, revoke,
etc.) must require an explicit confirmation parameter:

```python
@mcp.tool()
def delete_database(db_name: str, confirm: bool = False) -> dict:
    """Delete a database permanently.

    Args:
        db_name: Database name.
        confirm: Must be True to proceed. Defaults to False.
    """
    if not confirm:
        return {
            "error": "Destructive action requires confirm=True",
            "action": "delete_database",
            "target": db_name,
            "code": 400,
        }
    # proceed with deletion
```

### What counts as destructive

- HTTP DELETE methods
- Database DROP/TRUNCATE operations
- Key/secret rotation or revocation
- Bulk updates affecting many records
- Account deactivation or suspension
- Resource deprovisioning

## Structured Error Payloads

Never return raw strings or stack traces. Use a consistent error shape:

```json
{
  "error": "Human-readable description of what went wrong",
  "code": 404,
  "details": {
    "resource": "item",
    "id": "abc-123"
  }
}
```

### Error mapping from HTTP status codes

| HTTP Status | MCP Error Behavior |
| --- | --- |
| 400 Bad Request | Return error with validation details |
| 401 Unauthorized | Return error suggesting credential check |
| 403 Forbidden | Return error with required permission |
| 404 Not Found | Return error with resource identifier |
| 409 Conflict | Return error with conflict description |
| 429 Rate Limited | Return error with retry-after hint |
| 500+ Server Error | Return error, do not expose internals |

### Never expose

- Stack traces
- Internal hostnames or IPs
- Database connection strings
- Raw exception messages from upstream APIs

## Rate Limiting

MCP servers should respect upstream API rate limits:

```python
import time

class RateLimiter:
    def __init__(self, max_per_second: float = 10.0):
        self._min_interval = 1.0 / max_per_second
        self._last_call = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.monotonic()
```

### Guidelines

- Read rate limit headers from API responses (`X-RateLimit-Remaining`,
  `Retry-After`) and back off accordingly
- Log rate limit events so users can tune request volume
- For batch operations, implement client-side throttling
- Return structured errors when rate limited, including estimated wait time
