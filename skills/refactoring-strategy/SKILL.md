---
name: refactoring-strategy
description: >
  Systematic refactoring methodology with safety guarantees for polyglot codebases.
  TRIGGER when: user asks to refactor code, restructure a module, split a monolith,
  do a large rename, extract a service, apply strangler fig, or plan a safe migration
  of existing code. Also when tech-debt-tracker findings need execution.
  DO NOT TRIGGER when: user is fixing a bug (use focused-fix), doing TDD on new code
  (use tdd), or finding tech debt without a plan to fix it (use tech-debt-tracker).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: refactoring, migration, strangler-fig, characterization-tests, large-scale, safety
---

> **You are a Principal Refactoring Engineer** -- you never touch code without characterization tests, you never mix behavior changes with structural changes, and you treat every commit as independently revertable.

# refactoring-strategy

Systematic refactoring with safety guarantees. From single-module cleanup to
monolith decomposition.

## What You Get

- Characterization test plan pinning current behavior before any changes
- Phased refactoring plan with individually revertable commits
- Impact analysis identifying downstream consumers and blast radius
- Rollback strategy for each phase

## The Iron Rules

1. **Characterization tests BEFORE any edit.** If you cannot test it, you
   cannot safely change it. See `characterization-tests.md`.
2. **Never mix behavior changes with structural changes.** Each commit is
   either a refactor (same behavior, new structure) or a feature (new behavior).
   Never both. This makes every commit individually revertable.
3. **Run the full suite after every commit.** Not just the tests you think are
   related. Refactoring reveals hidden coupling.

## Workflow

### Phase 1: Scope and Impact Analysis

Before touching code:

1. **Map the blast radius.** Use Explore agents to find all callers, importers,
   and consumers of the code you plan to change.
2. **Identify the abstraction boundary.** Is the current boundary wrong (need
   to redraw it) or is the implementation behind the boundary messy (can refactor
   without changing the interface)?
3. **Decide: refactor or rewrite?** See the decision tree below.

### Phase 2: Characterization Tests

Write tests that pin the current behavior. These are NOT aspirational tests for
the new design -- they document what the code does NOW, warts and all. See
`characterization-tests.md` for patterns.

### Phase 3: Plan the Refactoring

Choose a pattern from `patterns.md` (extract, inline, move, rename) or
`large-scale.md` (strangler fig, branch by abstraction, expand/contract).

Break the work into commits where each commit:
- Changes structure OR behavior, never both
- Leaves the test suite GREEN
- Can be reverted independently without breaking other commits

### Phase 4: Execute

For each planned commit:

1. Make the structural change
2. Run the full test suite
3. If GREEN, commit with a descriptive message
4. If RED, diagnose: is it a test that depended on structure (update the test)
   or did you accidentally change behavior (revert and try a smaller step)?

### Phase 5: Verify and Clean Up

1. Run the full test suite one final time
2. Remove characterization tests that are now redundant (covered by proper tests)
3. Update documentation, imports, and cross-references
4. Review the diff as a whole -- does the new structure match the original intent?

## Refactor vs Rewrite Decision Tree

```
Is the public interface (API, function signatures, module boundary) correct?
  |
  Yes --> Refactor the internals. Keep the interface, improve the implementation.
  No  --> Is the interface used by fewer than 5 callers?
    |
    Yes --> Rewrite with a new interface. Migrate callers one by one.
    No  --> Use Strangler Fig pattern. Build new interface alongside old,
            migrate callers incrementally, remove old when empty.
```

**Default to refactoring.** Rewrites feel productive but lose encoded behavior
that tests don't cover. Only rewrite when the abstraction boundary itself is wrong.

## Common Pitfalls

| Mistake | Fix |
|---------|-----|
| Refactoring without characterization tests | Stop. Write tests first. Always. |
| Mixing behavior + structure in one commit | Separate into two commits. No exceptions. |
| Refactoring code you don't understand | Read it first. Trace the data flow. Map callers. |
| "While I'm here" scope creep | Finish the planned refactoring. File a follow-up for new ideas. |
| Large PRs that can't be reviewed | Break into a chain of small PRs, each independently mergeable |
| Rewriting when refactoring would work | Use the decision tree. Rewrites lose implicit behavior. |

## Reading guide

| Topic | File |
|-------|------|
| Characterization test patterns | `characterization-tests.md` |
| Refactoring patterns (extract, inline, move, rename) | `patterns.md` |
| Large-scale strategies (strangler fig, expand/contract) | `large-scale.md` |

## See also

- `tech-debt-tracker` -- finds what to refactor; this skill says how
- `focused-fix` -- reactive bug fixing; this skill is proactive improvement
- `tdd` -- TDD workflow; its refactoring sub-file covers post-TDD smell cleanup within a module
- `architect` -- architecture analysis; pair with this skill when the refactoring changes module boundaries
