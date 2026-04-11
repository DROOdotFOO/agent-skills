---
title: Code Quality Checks and Scoring
impact: HIGH
impactDescription: Poor code quality increases defect rate and maintenance cost over time
tags: quality,solid,complexity,code-smells,scoring
---

# Code Quality Checks and Scoring

Detect SOLID violations, code smells, and complexity issues. Produce a quality score (0-100) with a verdict.

## SOLID Violations

### Single Responsibility (SRP)

- **God class**: >20 public methods or >500 lines. The class does too many things.
- **God function**: >50 lines. Break into smaller, named steps.
- **Mixed concerns**: A single file handles HTTP routing, business logic, and database access.
- **Flag**: class/module name contains "Manager", "Handler", "Processor", "Utils" with >10 methods.

### Open/Closed (OCP)

- **Switch on type**: `switch typeof` / `if isinstance` chains that grow with each new type. Use polymorphism or a registry.
- **Shotgun modification**: Adding a new feature requires changes in 5+ files following the same pattern.

### Liskov Substitution (LSP)

- **Broken contract**: Subclass raises exception parent doesn't, or silently ignores parent's required behavior.
- **Type narrowing**: Override method accepts fewer input types than parent.

### Interface Segregation (ISP)

- **Fat interface**: Interface/protocol with >7 methods where most implementors stub half of them.
- **Forced dependency**: Implementing a trait/interface requires pulling in unrelated dependencies.

### Dependency Inversion (DIP)

- **Concrete coupling**: Business logic directly instantiates infrastructure (database clients, HTTP clients, file I/O) instead of accepting interfaces/protocols.
- **Import direction**: High-level module imports from low-level module. Dependencies should point inward.

## Code Smells

### Complexity

| Smell                  | Threshold         | Severity |
|------------------------|--------------------|----------|
| Function length        | >50 lines          | MEDIUM   |
| Class/module length    | >500 lines         | MEDIUM   |
| Class method count     | >20 public methods | HIGH     |
| Nesting depth          | >4 levels          | HIGH     |
| Cyclomatic complexity  | >10 per function   | HIGH     |
| Parameter count        | >5 parameters      | MEDIUM   |
| Boolean parameters     | any                | LOW      |

### Duplication

- **Copy-paste blocks**: 6+ lines duplicated across 2+ locations. Extract to a shared function.
- **Similar structure**: Different functions following the same pattern with minor variations. Extract the pattern.

### Naming

- **Ambiguous names**: `data`, `result`, `temp`, `val`, `x` -- name should convey intent.
- **Misleading names**: `isValid` that also mutates state. Name should match behavior.
- **Inconsistent conventions**: Mix of `camelCase` and `snake_case` in the same file (unless language convention requires it).

### Error Handling

- **Swallowed errors**: Empty `catch {}`, `except: pass`, `_ -> :ok` with no logging.
- **Generic catches**: `catch (Exception e)` / `except Exception` without re-raising specific errors.
- **Missing error paths**: Function returns result but caller never checks for error case.
- **Panic in library code**: `unwrap()`, `panic!()`, `os.Exit()` in code that should return errors.

### Dead Code

- **Unreachable branches**: Code after unconditional return/break/continue.
- **Unused exports**: Public functions/types with zero importers (check with IDE or grep).
- **Commented-out code**: Remove it; version control has history.

## Quality Scoring Rubric

Score each category (0-20 points each), sum for total (0-100):

| Category          | 20 pts (excellent)           | 10 pts (acceptable)          | 0 pts (poor)                |
|-------------------|------------------------------|------------------------------|-----------------------------|
| **Correctness**   | Logic is sound, edge cases handled | Minor edge cases missed  | Bugs in core logic          |
| **Security**      | No vulnerabilities found     | Low-severity issues only     | CRITICAL/HIGH findings      |
| **Design**        | Clean abstractions, SOLID    | Minor violations, acceptable coupling | God classes, spaghetti |
| **Testing**       | New code fully tested        | Partial coverage, happy path | No tests for changes        |
| **Maintainability** | Clear naming, small functions, documented decisions | Some long functions, minor smells | Deep nesting, duplication, unclear intent |

## Verdict Thresholds

| Score   | Verdict          | Action                                  |
|---------|------------------|-----------------------------------------|
| 80-100  | PASS             | Approve. Minor suggestions optional.    |
| 60-79   | CONDITIONAL PASS | Approve after SHOULD FIX items addressed|
| 0-59    | FAIL             | Request changes. MUST FIX items present.|

## Reporting

```
Quality Score: 72/100 -- CONDITIONAL PASS
  Correctness:    16/20  (edge case in date parsing)
  Security:       20/20
  Design:         14/20  (UserService SRP violation, 23 methods)
  Testing:        12/20  (no tests for error paths)
  Maintainability: 10/20 (3 functions >50 lines, nesting depth 5)
```
