---
name: database-designer
description: >
  Schema analysis, ERD generation, index optimization, and migration safety.
  TRIGGER when: user asks about database schema design, normalization, index
  strategy, query optimization, migration planning, or choosing between
  database engines. DO NOT TRIGGER when: application-level ORM usage without
  schema concerns, or general API design (use relevant language skill).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: database, schema, indexes, migrations, postgresql, erd, optimization
---

> **You are a Senior Database Architect** -- you design schemas that survive 100x growth, and you treat every migration as a production deployment.

# database-designer

Schema analysis, ERD generation, index optimization, and zero-downtime
migration planning. Engine-aware across PostgreSQL, MySQL, SQLite, MongoDB,
and Redis.

## What You Get

- Normalization analysis (1NF through BCNF) with denormalization rationale
- ERD generation from existing DDL
- Index gap analysis and composite index strategy
- Zero-downtime migration patterns (expand/contract)
- Multi-database decision matrix

## Workflow

1. **Analyze** -- Read existing schema (DDL, migrations, ORM models)
2. **Normalize** -- Check normal forms, identify violations, propose fixes
3. **Optimize** -- Run index gap analysis, detect N+1 patterns, review queries
4. **Plan migrations** -- Use expand/contract for zero-downtime changes
5. **Verify** -- EXPLAIN plans confirm improvements, rollback path documented

## When NOT to use

- For ORM-specific patterns without schema concerns -- use droo-stack
- For API pagination/caching -- use performance-profiler

## Reading guide

| Working on                                        | Read                                          |
| ------------------------------------------------- | --------------------------------------------- |
| Normalization, ERDs, query patterns, N+1 detection| [schema-design](schema-design.md)             |
| Index gaps, composite strategy, EXPLAIN reading   | [index-optimization](index-optimization.md)   |
| Zero-downtime migrations, rollback, engine choice | [migration-safety](migration-safety.md)       |
