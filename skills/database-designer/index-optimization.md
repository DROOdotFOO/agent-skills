---
title: Index Optimization
impact: CRITICAL
impactDescription: correct indexing is the single largest factor in query performance
tags: indexes, btree, gin, gist, partial, covering, explain, connection-pooling
---

# Index Optimization

## Gap analysis process

1. Collect slow queries (pg_stat_statements, slow query log)
2. Run EXPLAIN ANALYZE on each
3. Look for Seq Scan on large tables, high row estimates vs actual
4. Cross-reference WHERE/JOIN/ORDER BY columns against existing indexes
5. Propose missing indexes, flag redundant ones

## Composite index strategy

Column order matters. Place columns in this priority:

1. **Equality conditions first** (`WHERE status = 'active'`)
2. **Range conditions next** (`WHERE created_at > '2026-01-01'`)
3. **ORDER BY / GROUP BY last**

```sql
-- Query: WHERE tenant_id = ? AND status = ? AND created_at > ? ORDER BY created_at
CREATE INDEX idx_orders_tenant_status_created
    ON orders (tenant_id, status, created_at);
```

A composite index on `(a, b, c)` satisfies queries on `(a)`, `(a, b)`, and
`(a, b, c)` but NOT `(b)` or `(b, c)` alone.

## Redundancy detection

An index on `(a)` is redundant if `(a, b)` exists. Drop the shorter one
unless it is significantly smaller and used by a hot query path.

Check with:

```sql
SELECT indexrelid::regclass, indkey
FROM pg_index
WHERE indrelid = 'my_table'::regclass
ORDER BY indkey;
```

## Index type selection

| Type     | Use for                                          | Example                                  |
| -------- | ------------------------------------------------ | ---------------------------------------- |
| B-tree   | Equality, range, sorting (default)               | `CREATE INDEX ... ON t (col)`            |
| GIN      | Full-text search, JSONB containment, arrays      | `CREATE INDEX ... USING gin (col)`       |
| GiST     | Geometry, range types, nearest-neighbor           | `CREATE INDEX ... USING gist (col)`      |
| Partial  | Subset of rows (reduces index size)              | `... WHERE status = 'active'`            |
| Covering | Include non-indexed columns (index-only scans)   | `... INCLUDE (email, name)`              |

### Partial index example

```sql
-- Only index active orders (90% of queries filter on this)
CREATE INDEX idx_orders_active ON orders (user_id, created_at)
    WHERE status = 'active';
```

### Covering index example

```sql
-- Avoid heap lookups for common SELECT columns
CREATE INDEX idx_users_email_covering ON users (email) INCLUDE (name, avatar_url);
```

## Reading EXPLAIN output

Key fields to check:

| Field           | Good                        | Bad                              |
| --------------- | --------------------------- | -------------------------------- |
| Scan type       | Index Scan, Index Only Scan | Seq Scan on large table          |
| Rows (estimate) | Close to actual             | Off by 10x+ (stale statistics)  |
| Buffers         | Shared hit (cached)         | Shared read (disk I/O)          |
| Sort method     | Index, quicksort            | External merge (disk sort)       |

Run `ANALYZE table_name` if estimates are wildly off. Check `n_distinct` and
`correlation` in `pg_stats` for problem columns.

## Connection pooling

### When to use

Always in production. Database connections are expensive (fork + TLS
handshake + memory). Pool at the application or proxy layer.

### Tools

| Tool       | Language/Platform    | Notes                                    |
| ---------- | -------------------- | ---------------------------------------- |
| PgBouncer  | PostgreSQL           | Transaction-mode pooling, low overhead   |
| ProxySQL   | MySQL                | Query routing, caching, failover         |
| HikariCP   | JVM (Java/Kotlin)    | Fast, well-tuned defaults                |
| Ecto pools | Elixir               | Built-in via DBConnection                |

### Sizing formula

```
pool_size = (core_count * 2) + effective_spindle_count
```

For SSDs, `effective_spindle_count` is typically 1. A 4-core server: pool of
~9. Start there and adjust based on `pg_stat_activity` wait events.
