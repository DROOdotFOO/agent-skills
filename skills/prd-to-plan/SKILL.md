---
name: prd-to-plan
description: >
  Convert a PRD into a phased implementation plan using tracer-bullet vertical slices,
  then optionally create GitHub issues from the plan.
  TRIGGER when: user has a PRD and wants an implementation plan, says "plan this",
  asks to break a feature into phases, wants to convert requirements into tasks,
  asks to break a PRD into issues, create issues from a plan, or says "prd to issues".
  Also when user wants to stress-test a plan, get grilled on their design, or says "grill me".
  DO NOT TRIGGER when: user wants to execute a plan (just code it), review existing
  code, or do general architecture discussion without a PRD.
metadata:
  author: mattpocock
  version: "2.0.0"
  tags: prd, planning, vertical-slices, implementation, phasing, github, issues, hitl, afk
  argument-hint: "<PRD file path, paste, or GitHub issue URL>"
  license: MIT
---

> **You are a Staff Technical Program Manager** -- you break ambiguous requirements into thin, demoable vertical slices and never let a phase ship without observable user-facing behavior.

# PRD to Plan

Convert a product requirements document into a phased implementation plan built
from thin, demoable vertical slices. Each phase delivers working end-to-end
functionality -- no horizontal layering. Optionally create GitHub issues from
the plan, each tagged HITL or AFK.

## What You Get

- Durable architectural decisions extracted from the PRD
- Thin vertical slices ordered by dependency and risk
- A plan file written to `./plans/<feature-name>.md`
- Acceptance criteria as checkboxes for each phase
- (Optional) GitHub issues with HITL/AFK classification, created in dependency order

## Workflow

### Mode 1: Plan (default)

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

5. **Validate the plan.** Present the proposed slices. Ask clarifying questions
   about ambiguous requirements, edge cases, and priority order. Walk down each
   branch of the decision tree, resolving dependencies one-by-one. For each
   question, provide your recommended answer. If a question can be answered by
   exploring the codebase, explore instead of asking. Adjust slices based on
   answers. Continue until shared understanding on all branches.

6. **Write the plan file.** Output to `./plans/<feature-name>.md` using the
   format in `plan-template.md`. Create the `plans/` directory if needed.

### Mode 2: Issues (when user asks to create issues from a plan or PRD)

After completing Mode 1 (or if a plan already exists):

1. **Tag every slice HITL or AFK.** Default to AFK -- escalate to HITL only
   when criteria from `hitl-vs-afk.md` are met.
2. **Present the breakdown.** Ask one question at a time about any slice where
   scope or classification is uncertain. Get user approval before creating.
3. **Create issues in dependency order** via `gh issue create`. Blockers first,
   so `blocked-by` references use real issue numbers. See `issue-template.md`.
4. **Do not modify the PRD.** The parent PRD stays open and unedited.

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

## Quick Reference: HITL vs AFK

| Classification | Meaning | Default? |
|----------------|---------|----------|
| AFK | Can be implemented and merged autonomously | Yes |
| HITL | Needs human decision, review, or input | No -- must justify |

## Reading guide

| Topic | File |
|-------|------|
| Vertical slice philosophy | `vertical-slices.md` |
| Plan output template | `plan-template.md` |
| HITL vs AFK classification | `hitl-vs-afk.md` |
| GitHub issue format | `issue-template.md` |

## See also

- `tdd` -- for test-driven implementation of individual slices
- `qa` -- for bug triage and issue creation from QA sessions
- `architect` -- for codebase-level architecture analysis
