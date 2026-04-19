---
title: TDD Fix Plan
impact: CRITICAL
impactDescription: A weak fix plan leads to incomplete fixes, regressions, or fixes that cannot be verified
tags: tdd, fix-plan, red-green, issues, vertical-slice
---

# TDD Fix Plan

## Structure

A TDD fix plan is a sequence of RED-GREEN cycles embedded in the GitHub issue body. Each cycle is one vertical slice: write a failing test, then make it pass. The cycles are ordered so each builds on the last.

## Principles

**Tests verify behavior through public interfaces.** A test that calls internal methods will break on refactor and provide false confidence. Test what the caller sees.

**Tests should survive internal refactors.** If you rename a private function and a test breaks, the test was wrong. Tests pin behavior, not implementation.

**Each cycle is independently verifiable.** After completing cycle N, all tests (including previous cycles) must pass. If cycle N breaks cycle N-1, the slice was too big.

**Cycles are ordered by dependency.** Start with the simplest reproduction of the bug, then layer on edge cases and related fixes.

## Issue Body Template

```markdown
## Bug

**Expected**: [what should happen]
**Actual**: [what happens instead]
**Reproduction**: [command, input, or steps]

## Root Cause

[1-2 sentences describing why the bug happens, referencing module/behavior not file paths]

## Fix Plan (TDD)

### Cycle 1: Reproduce the bug as a failing test

**RED**: Write a test that [describes the expected behavior in plain English].
The test calls [public function/endpoint] with [input] and asserts [expected output].
This test should fail because [reason].

**GREEN**: [Describe the minimal code change to make this test pass].

### Cycle 2: [Edge case or related behavior]

**RED**: Write a test that [describes the next behavior to verify].
This test should fail because [reason].

**GREEN**: [Describe the change].

### Cycle 3: [Additional edge case if needed]

...

## Verification

After all cycles:
- [ ] All new tests pass
- [ ] Full test suite passes (no regressions)
- [ ] The original reproduction steps no longer exhibit the bug
```

## Guidance for Writing Cycles

**Cycle 1 is always the direct reproduction.** Convert the bug report's reproduction steps into a test. This is the most important cycle -- if you cannot reproduce the bug as a test, you do not understand it yet.

**Subsequent cycles cover**:
- Edge cases related to the same root cause
- Boundary conditions (empty input, max values, concurrent access)
- Behaviors that share the same code path and might regress

**Keep cycles small.** If a cycle requires more than ~20 lines of implementation, split it. The point is incremental confidence, not batch fixing.

**Do not include refactoring cycles in the issue.** Refactoring happens after all tests are green and is a separate concern. The issue tracks the fix, not the cleanup.
