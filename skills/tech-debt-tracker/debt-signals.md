---
title: Debt Signals
impact: HIGH
impactDescription: Missing debt signals means untracked degradation compounds silently
tags: tech-debt,scanning,code-smells,static-analysis
---

# Debt Signals

What to scan for when identifying tech debt across a codebase.

## Comment-based Signals

Scan for marker comments that developers leave as breadcrumbs:

- `TODO` -- Planned work that was deferred
- `FIXME` -- Known bugs or incorrect behavior
- `HACK` / `WORKAROUND` -- Intentional shortcuts
- `XXX` -- Dangerous or fragile code
- `TEMP` / `TEMPORARY` -- Code meant to be replaced
- `DEPRECATED` -- Still present but should not be used

Extract context: the comment text, surrounding function, file age (git blame), and author. Old TODOs (>6 months) are higher priority than recent ones.

## Structural Signals

### Long functions

Functions exceeding 50 lines (excluding comments and blank lines). Indicates multiple responsibilities. Threshold varies by language: 50 for most, 30 for functional languages, 80 for test setup.

### High cyclomatic complexity

Cyclomatic complexity above 10 per function. Count decision points: `if`, `else if`, `case`, `while`, `for`, `&&`, `||`, `catch`, ternary operators. Each adds 1 to base complexity of 1.

### Deep nesting

Indentation depth exceeding 4 levels. Signals complex conditional logic that should be flattened via early returns, guard clauses, or extraction.

### Duplicated code

Near-identical blocks (>10 lines or >3 occurrences). Look for copy-paste patterns where only variable names differ. Structural duplication (same algorithm, different types) also counts.

### Dead code

- Unreachable branches (always-true/false conditions)
- Unused exports, functions, classes, or variables
- Commented-out code blocks (>5 lines)
- Feature flags that are permanently on/off

### Hardcoded values

Magic numbers, string literals for configuration, embedded URLs, hardcoded credentials or API keys, environment-specific values outside config files.

## Dependency Signals

- **Outdated packages** -- Major versions behind, especially with known CVEs
- **Deprecated APIs** -- Using library functions marked for removal
- **Abandoned dependencies** -- No commits in 12+ months, unresponded issues
- **Version pinning without reason** -- Pinned to old versions with no comment explaining why
- **Transitive vulnerability** -- Deep dependency with known security issue

## Test Signals

- **Missing test coverage** -- Public functions or API endpoints with no tests
- **Test-to-code ratio** -- Below 0.5:1 for business logic modules
- **No edge case tests** -- Only happy path covered
- **Flaky tests** -- Tests that pass/fail intermittently (check CI history)
- **Slow tests** -- Individual tests exceeding 5 seconds

## Coupling Signals

- **God objects** -- Classes/modules with 10+ public methods or 500+ lines
- **Circular dependencies** -- Module A imports B which imports A
- **Shotgun surgery** -- A single logical change requires editing 5+ files
- **Feature envy** -- Function uses more data from another module than its own
- **Inappropriate intimacy** -- Module accesses internal details of another module

## Scanning Commands

```bash
# Comment markers
grep -rn "TODO\|FIXME\|HACK\|XXX\|WORKAROUND" --include="*.{ts,py,go,rs,ex}" .

# Long functions (rough heuristic -- count lines between function boundaries)
# Use language-specific tools: eslint, pylint, credo, golangci-lint

# Outdated dependencies
# npm outdated | pip list --outdated | mix hex.outdated | go list -m -u all

# Dead code
# ts-prune (TS) | vulture (Python) | deadcode (Go) | mix credo (Elixir)
```
