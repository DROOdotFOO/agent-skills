---
name: code-review
description: |
  Structured code review with blast radius analysis, security scanning, quality scoring, and a 30+ item checklist.
  TRIGGER when: user asks to review a PR, diff, changeset, or code for quality/security/breaking changes; user runs /review or /code-review; reviewing staged or committed changes.
  DO NOT TRIGGER when: writing new code from scratch, refactoring without review context, general debugging.
metadata:
  author: droo
  version: "1.0"
  tags: code-review,security,quality,blast-radius,breaking-changes,checklist
---

# Code Review Skill

Systematic code review following a fixed sequence: scope the change, assess blast radius, scan for security issues, verify tests, detect breaking changes, check performance, and score quality.

## Review Workflow

1. **Scope** -- Identify what changed (files, modules, services). Classify as feature, bugfix, refactor, config, or docs.
2. **Blast radius** -- Trace dependencies to determine how far the change reaches. See [blast-radius.md](blast-radius.md).
3. **Security scan** -- Run pattern-based checks for common vulnerabilities. See [security-scan.md](security-scan.md).
4. **Test coverage** -- Verify new/changed code has tests. Flag untested branches and edge cases.
5. **Breaking changes** -- Detect API, schema, config, and dependency changes that break consumers. See [breaking-changes.md](breaking-changes.md).
6. **Performance** -- Flag N+1 queries, unbounded loops, missing pagination, large allocations, blocking I/O on hot paths.
7. **Quality** -- Score SOLID adherence, complexity, and code smells. See [quality-checks.md](quality-checks.md).

Run the full [checklist](checklist.md) to ensure nothing is missed.

## Output Format

Organize findings into four categories with severity:

| Category     | Severity     | Meaning                                      |
|--------------|--------------|----------------------------------------------|
| MUST FIX     | CRITICAL/HIGH| Bugs, security holes, data loss risks         |
| SHOULD FIX   | HIGH/MEDIUM  | Design issues, missing tests, poor patterns   |
| SUGGESTIONS  | MEDIUM/LOW   | Style, naming, minor improvements             |
| LOOKS GOOD   | --           | Explicitly call out well-done aspects         |

Format each finding as:

```
[MUST FIX | SHOULD FIX | SUGGESTION] (severity) file:line
Description of the issue.
Recommended fix or alternative.
```

Always end with a summary: total findings by category, overall quality score (0-100), and a PASS / CONDITIONAL PASS / FAIL verdict.

## What You Get

- A structured review report with findings categorized as MUST FIX, SHOULD FIX, SUGGESTIONS, and LOOKS GOOD, each with severity and file location.
- Blast radius analysis showing how far the change reaches through dependency chains.
- A quality score (0-100) and a final verdict (PASS, CONDITIONAL PASS, or FAIL).

## Sub-files

| File                                       | Content                                    |
|--------------------------------------------|--------------------------------------------|
| [blast-radius.md](blast-radius.md)         | Dependency tracing, severity classification|
| [security-scan.md](security-scan.md)       | Vulnerability patterns, polyglot grep rules|
| [quality-checks.md](quality-checks.md)     | SOLID violations, smells, scoring rubric   |
| [checklist.md](checklist.md)               | Full 30+ item review checklist             |
| [breaking-changes.md](breaking-changes.md) | API, schema, config, dependency breakage   |
| [receiving-review.md](receiving-review.md) | How to evaluate and respond to review feedback |
