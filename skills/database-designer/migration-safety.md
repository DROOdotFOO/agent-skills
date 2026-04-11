---
title: Migration Safety
impact: CRITICAL
impactDescription: unsafe migrations cause downtime, data loss, or irreversible schema drift
tags: migrations, zero-downtime, expand-contract, rollback, database-selection
---

# Migration Safety

## Zero-downtime expand/contract pattern

Never rename or remove a column in a single deploy. Use three phases:

### Phase 1: Expand

Add the new column/table alongside the old one. Dual-write to both.

```sql
-- Migration: add new column
ALTER TABLE users ADD COLUMN display_name TEXT;

-- Application: write to both columns
UPDATE users SET display_name = username WHERE display_name IS NULL;
```

### Phase 2: Migrate

Backfill existing data. Verify new column is fully populated.

### Phase 3: Contract

Remove the old column after all readers have switched.

```sql
-- Only after verifying no code reads `username`
ALTER TABLE users DROP COLUMN username;
```

Each phase is a separate deploy. Minimum one deploy cycle between phases.

## Batch backfill

Never update millions of rows in a single transaction. Batch to avoid
lock contention and WAL bloat:

```sql
-- Backfill in batches of 10,000
DO $$
DECLARE
    batch_size INT := 10000;
    affected INT;
BEGIN
    LOOP
        UPDATE users
        SET display_name = username
        WHERE display_name IS NULL
        AND id IN (
            SELECT id FROM users WHERE display_name IS NULL LIMIT batch_size
        );
        GET DIAGNOSTICS affected = ROW_COUNT;
        EXIT WHEN affected = 0;
        COMMIT;
        PERFORM pg_sleep(0.1);  -- yield to other transactions
    END LOOP;
END $$;
```

## Rollback procedures

Every migration must have a documented rollback. For expand/contract:

| Phase    | Rollback action                          | Risk    |
| -------- | ---------------------------------------- | ------- |
| Expand   | Drop new column (safe, no data in it)    | Low     |
| Migrate  | Stop backfill, new column is partial     | Low     |
| Contract | Restore old column from backup           | HIGH    |

Keep backups of dropped columns for at least one release cycle:

```sql
-- Before dropping, snapshot to a recovery table
CREATE TABLE _recovery_users_username AS
    SELECT id, username FROM users;
```

## Dangerous operations

These acquire heavy locks in PostgreSQL. Avoid on large tables during traffic:

| Operation                        | Lock level         | Safe alternative                    |
| -------------------------------- | ------------------ | ----------------------------------- |
| `ALTER TABLE ... ADD COLUMN`     | ACCESS EXCLUSIVE*  | Safe if no DEFAULT (PG 11+)         |
| `ALTER TABLE ... SET NOT NULL`   | ACCESS EXCLUSIVE   | Add CHECK constraint, validate later|
| `CREATE INDEX`                   | SHARE              | `CREATE INDEX CONCURRENTLY`         |
| `ALTER TABLE ... ALTER TYPE`     | ACCESS EXCLUSIVE   | Expand/contract with new column     |

*PostgreSQL 11+ adds columns with DEFAULT without rewriting the table.

## Multi-database decision matrix

| Requirement                   | PostgreSQL | MySQL    | SQLite   | MongoDB  | Redis    |
| ----------------------------- | ---------- | -------- | -------- | -------- | -------- |
| ACID transactions             | +++        | ++       | ++       | +        | --       |
| Complex queries (CTEs, window)| +++        | ++       | +        | --       | --       |
| JSON document storage         | +++        | +        | +        | +++      | +        |
| Horizontal write scaling      | +          | +        | --       | +++      | ++       |
| Embedded / zero-config        | --         | --       | +++      | --       | --       |
| Caching / pub-sub             | +          | --       | --       | --       | +++      |
| Full-text search              | ++         | +        | +        | ++       | +        |
| Geospatial (PostGIS)          | +++        | +        | --       | ++       | +        |

Legend: `+++` excellent, `++` good, `+` adequate, `--` poor/unsupported.

**Default choice**: PostgreSQL unless you have a specific reason not to.
SQLite for embedded/CLI tools. Redis for caching/queues. MongoDB only when
document model genuinely fits and you do not need cross-document transactions.
