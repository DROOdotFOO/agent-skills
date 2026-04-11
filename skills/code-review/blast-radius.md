---
title: Blast Radius Analysis
impact: CRITICAL
impactDescription: Misclassifying blast radius leads to under-reviewed changes reaching production
tags: blast-radius,dependencies,imports,cross-service
---

# Blast Radius Analysis

Determine how far a change propagates through the codebase and across service boundaries.

## Tracing Method

1. **Direct dependents** -- Find all files that import/require the changed module. Use the language's import graph or grep for import statements.
2. **Transitive dependents** -- Follow the import chain one more level. If A imports B and B changed, A is affected.
3. **Cross-service boundaries** -- Check if the changed code is consumed via API, RPC, message queue, shared library, or database contract.
4. **Shared contracts** -- Identify protobuf definitions, OpenAPI specs, GraphQL schemas, database migrations, or shared type packages that multiple services depend on.
5. **Runtime coupling** -- Look for dynamic dispatch, reflection, event buses, or plugin systems where static analysis misses connections.

## Severity Classification

### CRITICAL -- Shared infrastructure

- Shared API contracts (protobuf, OpenAPI, GraphQL schemas)
- Authentication and authorization logic
- Payment processing, billing, financial calculations
- Database migration on tables used by multiple services
- Shared libraries published as packages
- Infrastructure-as-code (Terraform, Pulumi) for production
- CI/CD pipeline definitions

### HIGH -- Cross-module impact

- Changes to exported functions/types used by 3+ consumers
- Middleware, interceptors, or decorators on shared paths
- Configuration schema changes
- Shared utility modules (logging, error handling, validation)
- Database models referenced by multiple modules

### MEDIUM -- Single-module internal

- Internal refactor within one module with stable public API
- Adding new functionality behind a feature flag
- Test-only changes to existing test files
- Documentation updates for internal APIs

### LOW -- Isolated changes

- Leaf functions with no downstream dependents
- New files not yet imported anywhere
- Comment-only changes
- Dev tooling configs (.eslintrc, .prettierrc, Makefile)
- README and documentation files

## Assessing Blast Radius in Practice

```
# Find direct importers of a changed file
grep -r "import.*changed_module" --include="*.ts" -l
grep -r "from changed_module import" --include="*.py" -l
grep -r "require.*changed_module" --include="*.go" -l

# Check if file is part of a published package
# Look for: package.json exports, setup.py/pyproject.toml, go.mod module path
# If yes, all consumers of that package are in blast radius

# Check for cross-service communication
# Grep for HTTP clients calling endpoints defined in changed code
# Grep for message queue producers/consumers matching changed event types
```

## Reporting

State the blast radius classification (CRITICAL/HIGH/MEDIUM/LOW) and list the affected scope:

```
Blast radius: HIGH
Affected: 7 direct importers, 2 transitive, 0 cross-service
Key consumers: UserService, AuthMiddleware, AdminAPI
Risk: Changes to validation logic affect all user-facing endpoints
```
