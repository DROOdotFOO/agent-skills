---
title: GitHub Issue Template
impact: HIGH
impactDescription: Defines the consistent format for all issues created from a PRD
tags: github, issue, template, format, dependency
---

# GitHub Issue Template

Every issue created by this skill follows this format. Consistency matters --
it lets both humans and agents parse issues reliably.

## Title Format

```
[PRD-<parent>#<seq>] <imperative verb> <concise description>
```

- `<parent>` is the PRD issue number (or short identifier if the PRD is a file)
- `<seq>` is the sequence number in dependency order (1, 2, 3...)
- Imperative verb: "Add", "Implement", "Configure", "Wire up", "Extract"
- Keep under 72 characters

Examples:
- `[PRD-42#1] Add user authentication middleware`
- `[PRD-42#2] Implement token refresh endpoint`
- `[PRD-42#3] Wire up auth middleware to protected routes`

## Body Template

```markdown
## Parent PRD

Tracks #<parent-issue-number> (or link to PRD file)

## What to Build

<2-4 sentence description of this specific slice. What does it do, where does
it live in the codebase, what is the expected outcome.>

## Acceptance Criteria

- [ ] <concrete, testable criterion>
- [ ] <concrete, testable criterion>
- [ ] <concrete, testable criterion>
- [ ] Tests pass: <specific test file or pattern>

## Blocked By

- #<issue-number> -- <short reason>

(Omit this section if there are no blockers.)

## User Stories Addressed

- <paste or reference the specific user story from the PRD>

## Classification

**AFK** | **HITL -- [reason: <reason>]**
```

## Example Issue Body

```markdown
## Parent PRD

Tracks #42

## What to Build

Add a rate-limiting middleware to the API gateway. Apply a sliding-window
algorithm with configurable limits per route. Store counters in Redis using
the existing connection pool from `src/infra/redis.ts`.

## Acceptance Criteria

- [ ] Middleware rejects requests over the limit with 429 status
- [ ] Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining) are set
- [ ] Limits are configurable per route via `config/rate-limits.yaml`
- [ ] Tests pass: `tests/middleware/rate-limit.test.ts`
- [ ] Existing API tests still pass with middleware enabled

## Blocked By

- #101 -- Redis connection pool must be extracted to shared module first

## User Stories Addressed

- "As an API consumer, I receive clear feedback when I exceed rate limits"

## Classification

**AFK**
```

## Dependency Ordering in `gh issue create`

Issues must be created in dependency order so that `blocked-by` references
use real issue numbers. Follow this process:

1. **Topological sort.** Order slices so that every blocker appears before
   its dependents.
2. **Create blockers first.** Run `gh issue create` for issues with no
   dependencies. Capture the returned issue number.
3. **Substitute real numbers.** Replace placeholder references in dependent
   issues with the actual `#number` from step 2.
4. **Create dependents.** Run `gh issue create` for the next tier, using
   real issue numbers in the "Blocked By" section.
5. **Repeat.** Continue tier by tier until all issues are created.

Example creation sequence:

```bash
# Tier 0: no dependencies
gh issue create --title "[PRD-42#1] Extract Redis connection pool" \
  --body "..."
# Returns: #101

# Tier 1: depends on #101
gh issue create --title "[PRD-42#2] Add rate-limiting middleware" \
  --body "...Blocked By\n- #101..."
# Returns: #102

# Tier 1: depends on #101
gh issue create --title "[PRD-42#3] Add request logging middleware" \
  --body "...Blocked By\n- #101..."
# Returns: #103

# Tier 2: depends on #102 and #103
gh issue create --title "[PRD-42#4] Wire up middleware chain to gateway" \
  --body "...Blocked By\n- #102\n- #103..."
```

## Notes

- Do not add GitHub labels programmatically -- they require repo configuration.
  Use the in-body classification tag instead.
- If the repo uses a specific issue template, adapt the body to fit while
  preserving the required sections (Parent PRD, Acceptance Criteria,
  Classification).
- Always include at least 3 acceptance criteria. If you cannot write 3, the
  slice is too small -- merge it with an adjacent slice.
