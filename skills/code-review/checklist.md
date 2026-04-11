---
title: Code Review Checklist
impact: HIGH
impactDescription: A structured checklist prevents reviewers from missing categories of issues
tags: checklist,review,process,comprehensive
---

# Code Review Checklist

30+ items organized by category. Check each item and note findings.

## Scope (4 items)

- [ ] Change is clearly scoped -- single concern, not mixing features with refactors
- [ ] PR description explains the what and why
- [ ] Commit history is logical (atomic commits, no "fix fix fix" chains)
- [ ] Change type is identified: feature / bugfix / refactor / config / docs / dependency

## Blast Radius (4 items)

- [ ] Blast radius classified (CRITICAL / HIGH / MEDIUM / LOW)
- [ ] All direct dependents of changed code identified
- [ ] Cross-service impacts assessed (APIs, shared libs, message contracts)
- [ ] Shared contracts (protobuf, OpenAPI, GraphQL) reviewed for backward compatibility

## Security (8 items)

- [ ] No hardcoded secrets, API keys, or credentials
- [ ] No SQL injection via string interpolation
- [ ] No XSS vectors (innerHTML, dangerouslySetInnerHTML, document.write with user input)
- [ ] No eval/exec/command injection with user-controlled input
- [ ] No path traversal via unsanitized user paths
- [ ] Auth and authorization enforced on new/changed endpoints
- [ ] TLS verification not disabled (verify=False, InsecureSkipVerify)
- [ ] No prototype pollution vectors (JS/TS deep merge without prototype guard)

## Testing (5 items)

- [ ] New code has corresponding tests
- [ ] Modified code has updated tests reflecting the change
- [ ] Error paths and edge cases tested (not just happy path)
- [ ] Tests are deterministic (no flaky timing, random data, or external deps)
- [ ] Integration tests present for cross-module changes

## Breaking Changes (5 items)

- [ ] No removed or renamed public API endpoints/functions without deprecation
- [ ] No destructive database migrations (column drop, type change) without rollback plan
- [ ] No new required environment variables without documentation and defaults
- [ ] No dependency major version bumps without compatibility verification
- [ ] No config format changes that break existing deployments

## Performance (4 items)

- [ ] No N+1 query patterns (loop with individual queries instead of batch)
- [ ] No unbounded loops or missing pagination on list endpoints
- [ ] No unnecessary large allocations (loading full tables, unbounded arrays)
- [ ] No blocking I/O on hot paths or in async contexts without yielding

## Code Quality (7 items)

- [ ] No functions exceeding 50 lines
- [ ] No classes/modules exceeding 20 public methods
- [ ] No nesting deeper than 4 levels
- [ ] No cyclomatic complexity exceeding 10 per function
- [ ] No swallowed errors (empty catch/rescue blocks)
- [ ] No dead code (commented-out blocks, unreachable branches)
- [ ] Naming is clear and consistent with codebase conventions

## Documentation (3 items)

- [ ] Public API changes reflected in documentation
- [ ] Non-obvious logic has explanatory comments (why, not what)
- [ ] Migration steps documented for breaking changes

## Summary Template

```
Review: [PR title / changeset description]
Blast radius: [CRITICAL/HIGH/MEDIUM/LOW] -- [brief scope]
Findings: [N] MUST FIX, [N] SHOULD FIX, [N] SUGGESTIONS
Quality score: [0-100] -- [PASS / CONDITIONAL PASS / FAIL]

MUST FIX:
  1. ...

SHOULD FIX:
  1. ...

SUGGESTIONS:
  1. ...

LOOKS GOOD:
  - [things done well]
```
