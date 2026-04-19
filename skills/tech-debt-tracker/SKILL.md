---
name: tech-debt-tracker
description: |
  Automated tech debt scanning, classification, and cost-of-delay prioritization.
  TRIGGER when: user asks to find tech debt, audit code quality, prioritize refactoring, track debt trends, or assess code health; user runs /tech-debt or /debt-scan.
  DO NOT TRIGGER when: writing new features, doing code review (use code-review skill), debugging specific bugs.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: tech-debt,code-quality,refactoring,prioritization,cost-of-delay
---

# Tech Debt Tracker Skill

Systematic tech debt management: scan for debt signals, classify by type, prioritize using cost-of-delay, and track trends over time.

## Workflow

1. **Scan** -- Identify debt signals across the codebase. See [debt-signals.md](debt-signals.md).
2. **Classify** -- Categorize each finding (code debt, design debt, test debt, dependency debt, documentation debt).
3. **Prioritize** -- Rank findings using cost-of-delay frameworks. See [prioritization.md](prioritization.md).
4. **Report** -- Generate a debt inventory with actionable recommendations.
5. **Track** -- Compare against previous scans to measure debt trajectory (increasing, stable, decreasing).

## Debt Classification

| Type         | Examples                                          |
|--------------|---------------------------------------------------|
| Code         | Long functions, deep nesting, duplicated logic    |
| Design       | Tight coupling, missing abstractions, god objects |
| Test         | Missing coverage, flaky tests, no edge cases      |
| Dependency   | Outdated packages, deprecated APIs, pinned EOL    |
| Documentation| Stale comments, missing API docs, wrong examples  |

## Output Format

```
[DEBT] type=Code severity=HIGH file:line
Signal: Function exceeds 80 lines with cyclomatic complexity 14
Cost-of-delay: Blocks feature X, increases bug rate in module Y
Recommendation: Extract into 3 focused functions by responsibility
Priority: STRATEGIC (high value, high effort)
```

End with a summary: total debt items by type, priority distribution, top 5 recommendations, and trend direction if historical data exists.

## What You Get

- A debt inventory listing every finding with type, severity, file location, and cost-of-delay assessment
- Priority rankings using a strategic/tactical matrix so you know which debt to pay down first
- A summary with totals by type, priority distribution, top 5 recommendations, and trend direction versus prior scans

## Sub-files

| File                                   | Content                                  |
|----------------------------------------|------------------------------------------|
| [debt-signals.md](debt-signals.md)     | What to scan for across languages        |
| [prioritization.md](prioritization.md) | Cost-of-delay frameworks, priority matrix|

## See also

- `refactoring-strategy` -- once you know what debt to pay, this skill says how to pay it safely
