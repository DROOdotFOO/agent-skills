---
name: prd-to-plan
description: >
  Convert a PRD into a phased implementation plan using tracer-bullet vertical slices.
  TRIGGER when: user has a PRD and wants an implementation plan, says "plan this",
  asks to break a feature into phases, or wants to convert requirements into tasks.
  DO NOT TRIGGER when: user wants to execute a plan (just code it), review existing
  code, or do general architecture discussion without a PRD.
metadata:
  author: mattpocock
  version: "1.0.0"
  tags: prd, planning, vertical-slices, implementation, phasing
---

# PRD to Plan

Convert a product requirements document into a phased implementation plan built
from thin, demoable vertical slices. Each phase delivers working end-to-end
functionality -- no horizontal layering.

## What You Get

- Durable architectural decisions extracted from the PRD
- Thin vertical slices ordered by dependency and risk
- A plan file written to `./plans/<feature-name>.md`
- Acceptance criteria as checkboxes for each phase

## Workflow

1. **Confirm PRD in context.** Verify the PRD is loaded. If not, ask the user
   to provide it or point to the file.

2. **Explore the codebase.** Understand existing patterns: routing conventions,
   data layer, auth boundaries, component structure, test setup. The plan must
   fit the codebase, not fight it.

3. **Identify durable architectural decisions.** Extract decisions that will
   survive implementation: routes, DB schemas, model/type names, auth
   boundaries, third-party integrations. Omit volatile details (variable names,
   internal helper functions, CSS classes).

4. **Draft vertical slices.** Break the PRD into the thinnest possible
   end-to-end slices. Each slice must be independently demoable. Prefer many
   thin slices over few thick ones. See `vertical-slices.md` for the full
   philosophy.

5. **Quiz the user.** Present the proposed slices. Ask clarifying questions
   about ambiguous requirements, edge cases, and priority order. Adjust slices
   based on answers.

6. **Write the plan file.** Output to `./plans/<feature-name>.md` using the
   format in `plan-template.md`. Create the `plans/` directory if needed.

## Rules

- Each slice MUST be demoable on its own -- if you cannot show it working, it
  is too abstract or too coupled.
- Prefer many thin slices over few thick ones. A slice that takes more than a
  session to implement is too thick.
- DO include durable decisions: routes, schemas, model names, auth boundaries,
  third-party service choices.
- DO NOT include volatile implementation details: internal function names,
  variable naming, file organization within modules.
- Order slices by dependency (foundational first) then by risk (riskiest early).
- Every slice must state what user-visible behavior changes.
- The plan is a communication tool, not a specification. Keep it scannable.

## Anti-Patterns

- **Horizontal slicing**: "Phase 1: all database tables, Phase 2: all API
  routes, Phase 3: all UI." This delays feedback and hides integration risk.
- **Kitchen-sink phases**: a single phase with 15 acceptance criteria. Split it.
- **Premature optimization phases**: "Phase N: add caching." Only include if
  the PRD explicitly requires it.
- **Missing demo criteria**: if a phase has no observable output, it is not a
  vertical slice.
