---
title: HITL vs AFK Classification
impact: CRITICAL
impactDescription: Determines whether each issue requires human involvement or can be completed autonomously
tags: hitl, afk, classification, autonomy, planning
---

# HITL vs AFK Classification

Every issue created from a PRD must be tagged as either HITL (human-in-the-loop)
or AFK (autonomous/away-from-keyboard). The default is AFK.

## AFK (Autonomous)

An issue is AFK when an agent can implement it end-to-end and open a mergeable PR
without needing human decisions mid-flight.

**Criteria -- all must be true:**

- Acceptance criteria are concrete and testable
- Scope is well-defined with no ambiguity in what "done" means
- Implementation path is clear from the codebase and PRD
- No design decisions beyond what the PRD already specifies
- Can be verified by automated tests
- Touches only internal code (no public API surface changes that need sign-off)
- No security-sensitive logic (auth, crypto, permissions)

**Examples:**

- Add a utility function with specified inputs/outputs
- Write tests for an existing module
- Refactor internals without changing public behavior
- Add a CLI flag with defined behavior and help text
- Implement a data migration with a clear schema diff
- Wire up an existing API endpoint to the frontend per a mockup

## HITL (Human-in-the-Loop)

An issue is HITL when it requires a human decision, review, or judgment call
that cannot be derived from the PRD alone.

**Criteria -- any one is sufficient:**

- **Design decisions needed.** The PRD leaves a UX or architecture choice open
- **Security-sensitive.** Auth flows, permission models, crypto, key management
- **UX review required.** Visual design, user-facing copy, interaction patterns
- **Unclear requirements.** The PRD is ambiguous and needs clarification
- **Cross-team coordination.** Depends on another team's API, schedule, or approval
- **Breaking changes.** Public API modifications, data format changes, migrations
  that affect external consumers
- **Policy or compliance.** Touches legal, privacy, or compliance-sensitive areas

**Examples:**

- Design the error UX for a new feature (PRD says "handle errors gracefully")
- Choose between two authentication strategies
- Define the public API shape for a new module
- Review and approve a data migration that drops columns
- Coordinate with a partner team on an integration contract

## Decision Process

```
Start: Is every acceptance criterion concrete and testable?
  |
  No --> HITL (unclear requirements)
  Yes --> Does it touch security, auth, or crypto?
    |
    Yes --> HITL (security-sensitive)
    No --> Does it require design/UX decisions not in the PRD?
      |
      Yes --> HITL (design decisions needed)
      No --> Does it change a public API or external contract?
        |
        Yes --> HITL (breaking changes)
        No --> Does it need another team's input?
          |
          Yes --> HITL (cross-team coordination)
          No --> AFK
```

## Labeling in Issues

Add the classification as a tag in the issue body, not as a GitHub label
(labels require repo-level configuration).

```
**Classification:** AFK
```

or

```
**Classification:** HITL -- [reason: design decisions needed]
```

Always include the reason when marking HITL. This lets a human quickly decide
whether to engage or reclassify to AFK.
