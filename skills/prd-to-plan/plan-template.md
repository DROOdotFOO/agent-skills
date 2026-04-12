---
title: Plan Output Template
impact: HIGH
impactDescription: >
  Defines the structure of the output plan file. Inconsistent plan formats
  reduce scannability and make it harder to track progress.
tags: template, plan-format, output, documentation
---

# Plan Output Template

Every plan is written to `./plans/<feature-name>.md`. Create the `plans/`
directory if it does not exist. Use the structure below.

## Template

```markdown
# <Feature Name> -- Implementation Plan

> Source PRD: <path or link to PRD>

## Architectural Decisions

Durable decisions that guide all phases. These are commitments, not suggestions.

- **Routes**: <list routes with HTTP methods>
- **Database schema**: <table/collection names, key columns, relationships>
- **Models/Types**: <domain model names and their core fields>
- **Auth boundaries**: <which routes/actions require auth, role gates>
- **Third-party integrations**: <services, SDKs, API versions>
- **Key conventions**: <naming patterns, ID formats, anything the codebase already establishes>

---

## Phase 1: <Short Title>

**User stories covered**: <list story IDs or short descriptions>

**What to build**: <1-3 sentence description of the end-to-end behavior this
phase delivers. Focus on what changes from the user's perspective.>

**Acceptance criteria**:

- [ ] <Observable behavior or artifact, not an implementation step>
- [ ] <Another criterion>
- [ ] <Keep to 3-5 per phase>

---

## Phase 2: <Short Title>

**User stories covered**: ...

**What to build**: ...

**Acceptance criteria**:

- [ ] ...

---

(Continue for each phase.)
```

## Guidelines for Filling the Template

### Architectural Decisions

- Only include decisions that span multiple phases or constrain future work.
- Use the codebase's existing conventions. If the project uses `kebab-case`
  routes, do not introduce `camelCase` routes.
- Schema entries should name tables/columns but not specify index strategies
  or storage engines unless the PRD demands it.
- Auth boundaries should state what is protected, not how (unless the project
  has no existing auth and the PRD specifies a mechanism).

### Phase Sections

- Titles should be short enough to scan in a sidebar or table of contents.
- "What to build" describes the slice, not the steps. Write it as if explaining
  to a teammate what will be different after this phase ships.
- Acceptance criteria are checkboxes so progress can be tracked in the file.
  Each criterion must be verifiable by running the application or its tests.
- Avoid criteria like "refactor X" or "clean up Y" -- those are tasks, not
  observable outcomes.
- If a phase has more than 5 acceptance criteria, it is probably too thick.
  Split it.

### Naming the File

Use lowercase kebab-case derived from the feature name:

- "User Invoice Management" -> `plans/user-invoice-management.md`
- "OAuth2 Login Flow" -> `plans/oauth2-login-flow.md`
