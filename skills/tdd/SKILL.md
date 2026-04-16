---
name: tdd
description: |
  Test-driven development workflow for polyglot codebases.
  TRIGGER when: user asks to write tests first, do TDD, red-green-refactor, or requests test-driven implementation of a feature.
  DO NOT TRIGGER when: user asks to add tests after the fact, debug existing tests, or fix failing tests without a TDD workflow.
metadata:
  author: droo
  version: "1.0"
  tags: testing, tdd, red-green-refactor, test-driven, polyglot
---

# TDD Skill

## What You Get

- Failing test (RED) -> minimal implementation (GREEN) -> refactored code, committed at each green step
- Full test suite passing with no mocks of internal modules

## Philosophy

Tests verify **behavior through public interfaces**, not implementation details. Never test private methods directly. Never mock your own modules.

Use **vertical slices**, not horizontal slices. Write one test, make it pass, repeat. Do not write all tests first then implement -- that is waterfall disguised as TDD.

## Workflow: 4 Phases

### Phase 1: Planning

Before writing any code, confirm:
- What is the public interface (function signatures, module API)?
- What behaviors does the caller expect?
- What are the edge cases and error conditions?

Do NOT write code yet. Agree on the interface first.

### Phase 2: Tracer Bullet

Write exactly ONE test for the simplest happy-path behavior. Run it. Watch it fail (RED). Implement the minimum code to make it pass (GREEN). This proves the test infrastructure works end-to-end.

### Phase 3: Incremental Loop

For each remaining behavior:
1. Write ONE failing test (RED)
2. Implement minimum code to pass (GREEN)
3. If the code is messy, refactor NOW while green
4. Run the full suite -- all tests must pass
5. Repeat

Never skip ahead. Never write two tests before making the first green.

### Phase 4: Refactor

Only refactor when GREEN. Look for: duplication, shallow modules, long methods, feature envy, primitive obsession. Run the full suite after every refactor step.

## WRONG: writing all tests first

```python
# WRONG: this is waterfall disguised as TDD
def test_add(): ...
def test_subtract(): ...
def test_multiply(): ...
def test_divide(): ...
def test_divide_by_zero(): ...
# then implement all of Calculator at once
```

## CORRECT: one test at a time

```python
# RED: write one failing test
def test_add():
    assert Calculator().add(2, 3) == 5

# GREEN: implement minimum to pass
class Calculator:
    def add(self, a, b): return a + b

# next test only after green
def test_subtract():
    assert Calculator().subtract(5, 3) == 2
```

## Cycle Checklist

- [ ] Test describes a behavior, not an implementation detail
- [ ] Test uses the public API, not internal methods
- [ ] Test is RED before writing implementation
- [ ] Implementation is the minimum to go GREEN
- [ ] No new mocks of internal modules (only system boundaries)
- [ ] Full suite passes after going GREEN
- [ ] Refactor only while GREEN, re-run suite after each change

## Sub-files

| File | Topic |
|------|-------|
| [tests.md](tests.md) | Good vs bad test patterns with polyglot examples |
| [mocking.md](mocking.md) | When to mock, DI patterns per language |
| [mutation-testing.md](mutation-testing.md) | Mutation testing tools and interpretation |
| [deep-modules.md](deep-modules.md) | Deep vs shallow module design |
| [interface-design.md](interface-design.md) | Three principles for testable interfaces |
| [refactoring.md](refactoring.md) | Post-TDD refactor candidates |
