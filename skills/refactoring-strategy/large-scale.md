---
title: Large-Scale Refactoring Strategies
impact: HIGH
impactDescription: Large refactorings without an incremental strategy create merge conflicts, stale branches, and deployment risk
tags: strangler-fig, branch-by-abstraction, expand-contract, parallel, migration, monolith
---

# Large-Scale Refactoring Strategies

Patterns for refactorings that span multiple modules, services, or weeks.
The core principle: **every intermediate state must be deployable.**

## Strangler Fig

Replace a system incrementally by building the new version alongside the
old, migrating consumers one by one, then removing the old when it has
zero callers.

```
Phase 1: Build new implementation alongside old (both exist, old is active)
Phase 2: Route one consumer to new (both exist, partially migrated)
Phase 3: Route remaining consumers to new (old has zero callers)
Phase 4: Delete old implementation
```

**When to use:** Replacing a module, service, or subsystem where the public
interface is changing. Especially when the old code is too tangled to refactor
in place.

**Example:**

```python
# Phase 1: new parser exists alongside old
class LegacyParser:
    def parse(self, raw: str) -> dict: ...

class NewParser:
    def parse(self, raw: str) -> ParsedMessage: ...

# Phase 2: router directs traffic
def parse(raw: str, use_new: bool = False):
    if use_new:
        return NewParser().parse(raw)
    return LegacyParser().parse(raw)

# Phase 3: all callers use use_new=True (or default flipped)
# Phase 4: delete LegacyParser and the router
```

**Rules:**
- Old and new must coexist without interference
- Each phase is a separate PR that can be deployed independently
- Monitor both old and new paths during migration
- Delete the old code promptly after migration -- do not leave it "just in case"

## Branch by Abstraction

Introduce an abstraction layer, swap the implementation behind it, then
optionally remove the abstraction if it adds no lasting value.

```
Phase 1: Extract interface from existing implementation
Phase 2: Create new implementation of the interface
Phase 3: Switch consumers to new implementation
Phase 4: Remove old implementation (and interface, if not needed long-term)
```

**When to use:** Replacing an internal implementation while keeping the same
public contract. Database migrations, switching libraries, rewriting internals.

```elixir
# Phase 1: extract behaviour
defmodule App.Cache do
  @callback get(key :: String.t()) :: {:ok, term()} | :miss
  @callback put(key :: String.t(), value :: term(), ttl :: integer()) :: :ok
end

# Phase 2: old implementation conforms
defmodule App.Cache.ETS do
  @behaviour App.Cache
  def get(key), do: ...
  def put(key, value, ttl), do: ...
end

# Phase 3: new implementation
defmodule App.Cache.Redis do
  @behaviour App.Cache
  def get(key), do: ...
  def put(key, value, ttl), do: ...
end

# Phase 4: config switch
# config :app, cache: App.Cache.Redis
```

## Expand / Contract

Add the new capability (expand), migrate consumers, then remove the old
capability (contract). Commonly used for database schema changes.

```
Phase 1: EXPAND -- add new column/table/field (old still works)
Phase 2: MIGRATE -- write to both old and new, backfill historical data
Phase 3: SWITCH -- read from new, stop writing to old
Phase 4: CONTRACT -- remove old column/table/field
```

**When to use:** Database schema changes, API versioning, data format migrations.

```sql
-- Phase 1: EXPAND
ALTER TABLE users ADD COLUMN display_name VARCHAR(255);

-- Phase 2: MIGRATE (application code writes to both)
UPDATE users SET display_name = name WHERE display_name IS NULL;

-- Phase 3: SWITCH (application reads from display_name)

-- Phase 4: CONTRACT (after confirming no code reads 'name')
ALTER TABLE users DROP COLUMN name;
```

**Rules:**
- Each phase is a separate deployment
- Never drop the old column/field in the same deployment as adding the new one
- Backfill must be idempotent (safe to re-run)
- Monitor for errors between phases

## Parallel Implementation

Build the new version in a separate directory/module/service. Run both in
production, compare outputs, then cut over.

**When to use:** Critical systems where correctness must be verified before
switching (payment processing, data pipelines, search ranking).

```python
def process_payment(payment):
    old_result = legacy_processor.process(payment)
    new_result = new_processor.process(payment)

    if old_result != new_result:
        log.warning("Payment divergence", old=old_result, new=new_result)
        metrics.increment("payment.divergence")

    return old_result  # still using old until confidence is high
```

**Cutover criteria:**
- Zero divergences for N consecutive days
- New implementation handles all edge cases found in production
- Performance is equal or better

## Strategy Selection

| Situation | Strategy |
|-----------|----------|
| Replacing a public API or interface | Strangler Fig |
| Swapping an internal implementation | Branch by Abstraction |
| Database schema or data format change | Expand / Contract |
| Safety-critical system replacement | Parallel Implementation |
| Small module, good test coverage | Direct refactoring (patterns.md) |

## Common Pitfalls

| Mistake | Fix |
|---------|-----|
| Running both old and new code indefinitely | Set a deadline. Delete the old code. |
| Deploying expand + contract in one release | Separate deployments. Always. |
| No monitoring during migration | Add metrics for both paths. Alert on divergence. |
| Long-lived feature branch for the rewrite | Use strangler fig or branch by abstraction to merge incrementally |
| Skipping the parallel comparison phase | For critical systems, compare before cutting over |
