---
title: Port Allocation for Worktrees
impact: CRITICAL
impactDescription: prevents port collisions between parallel worktree sessions
tags: ports, docker-compose, worktree, isolation, networking
---

# Port Allocation for Worktrees

## Deterministic port formula

Every worktree gets a unique port range derived from its index:

```
port = base + (worktree_index * stride) + service_offset
```

Defaults: `base = 3000`, `stride = 100`, `service_offset` per service (0 for
web, 1 for API, 2 for DB, 3 for Redis, etc.).

| Worktree | Index | Web  | API  | DB   | Redis |
| -------- | ----- | ---- | ---- | ---- | ----- |
| main     | 0     | 3000 | 3001 | 3002 | 3003  |
| feature-a| 1     | 3100 | 3101 | 3102 | 3103  |
| feature-b| 2     | 3200 | 3201 | 3202 | 3203  |

## Persistence: .worktree-ports.json

Store allocations in the repo root (gitignored):

```json
{
  "base": 3000,
  "stride": 100,
  "worktrees": {
    "main": { "index": 0, "branch": "main", "created": "2026-01-15T10:00:00Z" },
    "feature-auth": { "index": 1, "branch": "feature/auth", "created": "2026-01-15T11:30:00Z" }
  }
}
```

When a worktree is removed, its index is recycled (use lowest available).

## Collision checks

Before claiming a port, verify it is free:

```bash
# Check if port is in use
lsof -i :"$port" -sTCP:LISTEN >/dev/null 2>&1 && echo "TAKEN" || echo "FREE"
```

If the deterministic port is taken by an external process, increment by 1 and
retry up to `stride - 1` times. Log a warning if fallback is needed.

## Docker Compose pattern

Use environment variables so the same `docker-compose.yml` works across
worktrees:

```yaml
services:
  web:
    ports:
      - "${WT_PORT_WEB:-3000}:3000"
  api:
    ports:
      - "${WT_PORT_API:-3001}:3001"
  db:
    ports:
      - "${WT_PORT_DB:-5432}:5432"
    volumes:
      - db-data-${WT_INDEX:-0}:/var/lib/postgresql/data

volumes:
  db-data-0:
  db-data-1:
  db-data-2:
```

Create a `.env` per worktree (gitignored) that sets `WT_INDEX`, `WT_PORT_WEB`,
`WT_PORT_API`, `WT_PORT_DB`.

## Validation checklist

Before declaring a worktree setup complete, verify all five:

1. [ ] Worktree directory exists and is on the correct branch
2. [ ] `.worktree-ports.json` updated with new entry
3. [ ] All allocated ports are free (lsof check passes)
4. [ ] `.env` file written with correct port variables
5. [ ] Services start and respond on allocated ports (`curl -sf http://localhost:$port/health`)
