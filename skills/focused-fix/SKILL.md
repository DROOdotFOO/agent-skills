---
name: focused-fix
description: >
  Structured 5-phase bug fix methodology with root cause verification.
  TRIGGER when: user wants to fix a bug, debug an issue, investigate a
  failure, or says "focused fix". Also when a fix attempt has failed and
  the user wants a systematic approach. DO NOT TRIGGER when: user wants
  architecture analysis (use architect), QA triage (use qa), or code
  review (use code-review).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: debugging, bug-fix, root-cause, methodology, verification
---

# focused-fix

Structured 5-phase bug fix methodology. No shortcuts.

## The Iron Law

**NO FIXES WITHOUT COMPLETING SCOPE -> TRACE -> DIAGNOSE FIRST.**

If you jump to a fix before completing the first three phases, you will:
- Fix symptoms, not causes
- Break something downstream
- Waste more time than you saved

## 5 Phases Overview

| Phase | Name | Purpose |
|-------|------|---------|
| 1 | SCOPE | Map the feature boundary -- what is this code supposed to do? |
| 2 | TRACE | Map all dependencies flowing in and out of the scoped area |
| 3 | DIAGNOSE | Systematically find every issue in the scoped area |
| 4 | FIX | Repair in strict order: deps -> types -> logic -> tests -> integration |
| 5 | VERIFY | All tests pass, including downstream consumers |

## 3-Strike Architecture Check

Before starting any fix, check if the bug reveals an architectural problem:

1. **Strike 1**: Is this the same kind of bug you have fixed before in this
   codebase? If yes, the architecture is inviting this bug class.
2. **Strike 2**: Would this bug be impossible if a dependency were inverted
   or an interface existed? If yes, note the architectural improvement.
3. **Strike 3**: Does fixing this bug require changing more than 3 files?
   If yes, the feature boundary is wrong.

If any strike hits, note the architectural issue. Fix the bug first (do not
refactor mid-fix), then file a follow-up issue for the architectural problem.

## Reading guide

| Working on | Read |
|-----------|------|
| Executing the 5 phases, risk labels, red flags, anti-patterns | [five-phases](five-phases.md) |
