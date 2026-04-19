---
title: Verification Before Completion
impact: HIGH
impactDescription: Skills that declare success without fresh evidence train Claude to claim completion without proof
tags: verification, completion, evidence, testing, quality
---

# Verification Before Completion

A cross-cutting pattern for workflow skills: never declare completion
without fresh evidence that the work actually succeeded.

## The Principle

Before reporting that a task is done, produce evidence:

- **Code change?** Run the test suite. Show the output.
- **Bug fix?** Reproduce the original bug, show it no longer occurs.
- **New feature?** Demonstrate it working, not just compiling.
- **Refactoring?** Show the test suite still passes.
- **Release?** Show the readiness checks passed.

"I believe this works" is not evidence. "Tests pass (output below)" is.

## How to Apply in Skills

Add a verification phase as the LAST step in any workflow skill that
produces a deliverable. The verification must:

1. **Be fresh** -- run the check NOW, not reference a previous run
2. **Be observable** -- show the output to the user, not just assert it
3. **Cover the claim** -- if you say "all tests pass," run ALL tests
4. **Catch regressions** -- run the full suite, not just the new tests

## Pattern for SKILL.md

In the workflow section, add a final phase:

```markdown
### Phase N: Verify

Before declaring the task complete:

1. Run the full test suite: `<project-specific command>`
2. Show the output (pass count, failure count)
3. If any tests fail, diagnose before declaring done
4. Confirm the original requirement is met (re-read it, don't paraphrase)
```

## Skills That Use This Pattern

- `focused-fix` -- Phase 5 (VERIFY): all tests pass, downstream consumers verified
- `qa` -- Phase 5 (Create Issue): reproduction steps verified before filing
- `release` -- Step 4 (Readiness checks): pre-release validation before tagging
- `tdd` -- Phase 3 (Incremental Loop): full suite after every GREEN step
- `refactoring-strategy` -- Phase 5 (Verify): full suite + characterization tests

## Anti-Patterns

| Pattern | Problem |
|---------|---------|
| "I've made the changes" without running tests | No evidence the change works |
| Running only the new test, not the full suite | Regressions hidden |
| "Tests should pass" based on reading the code | Belief is not evidence |
| Verifying once, then making more changes | Final state is unverified |
