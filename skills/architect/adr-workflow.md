---
title: ADR Workflow
impact: HIGH
impactDescription: Architecture Decision Record format, lifecycle management, pattern discovery, and maintenance
tags: adr, architecture, decisions, documentation
---

# ADR Workflow

## When to write an ADR

Write an ADR when:
- Adopting a new technology, framework, or library
- Changing an established pattern (e.g., switching from REST to gRPC)
- Making a trade-off with meaningful consequences (performance vs readability)
- Choosing between viable alternatives where the rationale is not obvious
- Reverting or superseding a previous decision

Do NOT write an ADR for:
- Obvious choices with no real alternatives
- Implementation details within an already-decided pattern
- Style preferences covered by linters/formatters

## ADR format

Store in `docs/adr/` as numbered files: `0001-use-event-sourcing.md`.

```markdown
# [NUMBER]. [TITLE]

Date: YYYY-MM-DD

## Status

[Proposed | Accepted | Deprecated | Superseded by ADR-NNNN]

## Context

What is the issue that we're seeing that is motivating this decision or change?
State the forces at play (technical, business, team, timeline).

## Decision

What is the change that we're proposing and/or doing?
State the decision in active voice: "We will..."

## Consequences

What becomes easier or harder because of this change?
List both positive and negative consequences. Be honest about trade-offs.
```

## Lifecycle management

- **Proposed** -- Under discussion, not yet accepted
- **Accepted** -- Team agrees, implementation can proceed
- **Deprecated** -- No longer relevant but kept for history
- **Superseded** -- Replaced by a newer ADR (link to it)

Never delete ADRs. Mark them superseded and link forward.

## Pattern discovery

When analyzing a codebase, identify which architectural pattern is in use:

| Pattern | Key indicators |
|---------|---------------|
| **Layered** | Controllers -> Services -> Repositories, strict layer dependencies |
| **Hexagonal** | Ports (interfaces) and adapters, domain has zero external imports |
| **Event-driven** | Message buses, event handlers, pub/sub, eventual consistency |
| **CQRS** | Separate read/write models, query handlers vs command handlers |
| **Microservices** | Independent deployables, API gateways, service discovery |
| **Modular monolith** | Single deployable, strict module boundaries, internal APIs |

When no clear pattern exists, note it. Mixed/absent patterns are common and
worth documenting in an ADR proposing a target architecture.

## Template for new ADRs

When generating an ADR:
1. Number sequentially from existing ADRs in `docs/adr/`
2. Title should be a short imperative phrase: "Use PostgreSQL for persistence"
3. Context should explain why the decision matters NOW
4. Decision should be concrete and actionable
5. Consequences should include at least one downside (no decision is free)
