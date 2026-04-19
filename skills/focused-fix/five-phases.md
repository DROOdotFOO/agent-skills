---
title: Five Phases
impact: CRITICAL
impactDescription: Complete 5-phase bug fix methodology with risk labeling, red flags, and anti-pattern detection
tags: debugging, phases, root-cause, verification, methodology
---

# Five Phases

## Phase 1: SCOPE

Map the feature boundary before touching anything.

- What is this feature supposed to do? (user-facing behavior)
- What are the inputs and outputs?
- What are the invariants that must hold?
- Where does this feature start and end in the codebase?

**Output**: A one-paragraph description of the feature boundary and its
invariants. If you cannot write this paragraph, you do not understand the
feature well enough to fix it.

## Phase 2: TRACE

Map all dependencies flowing in and out of the scoped area.

- What does this code call? (outbound dependencies)
- What calls this code? (inbound consumers)
- What shared state does it read or write?
- What external systems does it interact with?

**Output**: A dependency list with direction (in/out) for every dependency.
Mark each dependency with a risk label:

| Risk | Meaning |
|------|---------|
| HIGH | Change here could break consumers or corrupt shared state |
| MED | Change here requires updating tests or documentation |
| LOW | Change here is isolated, no downstream impact |

## Phase 3: DIAGNOSE

Systematically find every issue in the scoped area. Do not stop at the first
problem.

- Read every line in the scoped area
- Check each invariant from SCOPE -- is it maintained?
- Check each dependency from TRACE -- is it used correctly?
- Look for: off-by-one, null/nil handling, race conditions, missing error
  handling, wrong assumptions about input format

**Output**: A numbered list of every issue found, with risk label.

## Phase 4: FIX

Repair in strict order. This order exists because later fixes depend on
earlier ones being correct.

1. **Dependencies** -- Fix broken imports, version mismatches, missing deps
2. **Types** -- Fix type errors, schema mismatches, serialization bugs
3. **Logic** -- Fix the actual business logic bugs
4. **Tests** -- Update or add tests that cover every diagnosed issue
5. **Integration** -- Verify the fix works with real (not mocked) dependencies

After each sub-step, run the relevant test suite. Do not batch fixes and
test at the end.

## Phase 5: VERIFY

All tests pass. Not just the ones you touched. Show the evidence.

- Run the full test suite for the scoped module. Show the output.
- Run tests for every inbound consumer identified in TRACE
- If the fix changes an interface, verify all callers
- If the fix changes shared state, verify all readers
- Reproduce the original bug report and confirm it no longer occurs

The fix is not done until VERIFY passes. "I believe it works" is not
verification -- test output is.

## Red flags

Eight thoughts that mean you are skipping phases:

1. "I know what the problem is" -- You have not scoped yet
2. "Let me just try this quick fix" -- You have not traced dependencies
3. "The tests pass so it must be fine" -- You have not verified consumers
4. "This is just a typo" -- Typos do not cause bugs; misunderstandings do
5. "I will clean this up later" -- You will not
6. "This is not related" -- Prove it by checking the dependency trace
7. "The original code was wrong" -- Understand WHY it was written that way first
8. "I will add tests after" -- Tests written after a fix confirm the fix,
   not the correctness

## Anti-patterns

Eight forbidden behaviors during a focused fix:

1. **Shotgun fix** -- Changing multiple things at once to "see what sticks"
2. **Fix and pray** -- Making a change without running tests
3. **Scope creep** -- Refactoring unrelated code while fixing a bug
4. **Mock masking** -- Using mocks to make a broken test pass
5. **Copy-paste fix** -- Duplicating a fix across call sites instead of fixing
   the root cause
6. **Revert to green** -- Reverting to a passing state without understanding
   why the failure occurred
7. **TODO deferral** -- Leaving a TODO comment instead of fixing a diagnosed
   issue
8. **Blame shifting** -- Attributing the bug to an external dependency without
   verifying
