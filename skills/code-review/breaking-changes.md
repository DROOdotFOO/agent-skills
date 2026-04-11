---
title: Breaking Change Detection
impact: CRITICAL
impactDescription: Undetected breaking changes cause production incidents for downstream consumers
tags: breaking-changes,api,schema,migration,compatibility
---

# Breaking Change Detection

How to identify changes that break existing consumers, deployments, or integrations.

## API Contract Changes

### REST / HTTP

- **Removed endpoint**: Any DELETE of a route is breaking.
- **Renamed endpoint**: Path change without redirect or alias.
- **Changed HTTP method**: GET to POST, etc.
- **Removed/renamed response fields**: Consumers parsing the old shape will break.
- **Changed response field types**: String to number, object to array.
- **New required request fields**: Existing callers won't send them.
- **Changed status codes**: 200 to 201, or error code changes that consumers handle.
- **Changed error response format**: Different error body shape.

Detection: diff OpenAPI/Swagger specs. Compare route definitions, request/response schemas.

### gRPC / Protobuf

- **Removed fields**: Even if "unused," consumers may depend on them.
- **Changed field numbers**: Wire-incompatible.
- **Changed field types**: Int32 to int64, string to bytes.
- **Renamed services or methods**: Breaks generated client code.
- **Removed enum values**: Existing data with those values becomes undeserializable.

Detection: `buf breaking` or manual proto diff. Check field number stability.

### GraphQL

- **Removed fields or types**: Breaks client queries.
- **Changed field nullability**: Non-null to nullable or vice versa.
- **Changed argument types**: Existing queries become invalid.

Detection: diff schema SDL files. Use `graphql-inspector` or similar.

## Database Schema Changes

### Destructive Operations (always breaking)

- `DROP TABLE` / `DROP COLUMN`
- `ALTER COLUMN ... TYPE` (type change)
- `ALTER COLUMN ... SET NOT NULL` (on column with existing nulls)
- `RENAME TABLE` / `RENAME COLUMN`

### Safe Operations (non-breaking)

- `ADD COLUMN` with `DEFAULT` or `NULL`
- `CREATE TABLE`
- `CREATE INDEX` (may lock, but not breaking)
- `ADD COLUMN ... NOT NULL DEFAULT value` (Postgres 11+: no rewrite)

### Migration Safety Checklist

- Does the migration have a corresponding rollback/down migration?
- Can the migration run while the previous code version is still serving traffic? (deploy ordering)
- Does the migration lock tables used by hot-path queries?
- Is there a data backfill step, and can it run without downtime?

## Environment Variable Changes

- **New required env var**: Deployments without it will fail at startup.
- **Removed env var**: Code that reads it (in other services or scripts) will get empty/undefined.
- **Changed semantics**: Same name, different expected format or meaning.
- **Changed default value**: Code relying on old default behaves differently.

Detection: grep for `os.environ`, `process.env`, `System.get_env`, `os.Getenv` in changed files. Cross-reference with deployment configs, docker-compose, Kubernetes manifests.

## Dependency Changes

### Major Version Bumps

- Check changelog/migration guide for breaking changes in the dependency.
- Verify all usage sites are compatible with the new API.
- Run full test suite -- type checking alone is insufficient for runtime behavior changes.

### Removed Dependencies

- Verify no transitive consumer depends on the removed package.
- Check for peer dependency requirements.

### Lock File Conflicts

- `package-lock.json`, `yarn.lock`, `go.sum`, `mix.lock`, `Cargo.lock`: large diffs may indicate unintended transitive upgrades.

## Configuration Format Changes

- **Changed config file schema**: YAML/TOML/JSON structure changes break existing configs.
- **Renamed config keys**: Old configs become invalid.
- **Changed config file location**: Tools looking in old path will fail.
- **Changed CLI flag names**: Scripts using old flags break.

Detection: diff config file schemas, CLI argument parsers, and default config templates.

## Reporting Breaking Changes

For each detected breaking change, document:

```
BREAKING: [category] -- [description]
Affected: [list of consumers, services, or deployments]
Migration: [steps to update consumers]
Rollback: [how to revert if needed]
Deploy order: [which service deploys first]
```
