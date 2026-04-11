---
title: Prioritization Frameworks
impact: CRITICAL
impactDescription: Wrong prioritization wastes engineering time on low-impact debt while critical debt compounds
tags: tech-debt,prioritization,cost-of-delay,decision-matrix
---

# Prioritization Frameworks

How to decide which tech debt to pay down first using cost-of-delay analysis.

## Cost-of-Delay Dimensions

Evaluate each debt item on three axes:

### Interest Rate

How fast does this debt compound? Measured by how much harder the fix becomes over time.

- **HIGH** -- Every new feature built on top makes it worse (e.g., god object that every feature extends)
- **MEDIUM** -- Grows linearly with codebase size (e.g., duplicated code that gets copied again)
- **LOW** -- Static cost, fixing it costs the same now or in 6 months (e.g., rename a confusing variable)

### Blast Radius

How many features, teams, or services does this debt block or slow down?

- **HIGH** -- Shared infrastructure, core data models, authentication (affects all teams)
- **MEDIUM** -- Cross-module boundaries, shared utilities (affects 2-3 teams or features)
- **LOW** -- Isolated to a single module or feature (affects 1 team)

### Fix Cost Ratio (Now vs Later)

Compare the cost of fixing today versus fixing after N more features ship on top:

- **>3x** -- Fix cost will triple or more (architectural debt, schema changes)
- **1.5-3x** -- Moderate cost increase (growing test surface, more migration work)
- **~1x** -- Cost stays flat (cosmetic issues, naming, documentation)

## Priority Matrix

Combine the dimensions into four quadrants:

### Quick Win (Do First)

- Low effort, high value
- Interest rate: any | Blast radius: MEDIUM+ | Fix cost: low
- Examples: removing dead code, fixing a confusing API name used everywhere, adding missing index

### Strategic (Plan and Schedule)

- High effort, high value
- Interest rate: HIGH | Blast radius: HIGH | Fix cost: high
- Examples: decomposing a monolith module, migrating a data model, replacing a deprecated framework
- These need dedicated sprint time, not side-of-desk work

### Thankless (Defer or Automate)

- High effort, low value
- Interest rate: LOW | Blast radius: LOW | Fix cost: high
- Examples: rewriting working legacy code for style, migrating tests to a new framework
- Only tackle if you are already working in the area

### Urgent (Fix Now)

- Low effort, high value, time-sensitive
- Active breakage, security vulnerability, or blocking a release
- Examples: fixing a flaky test blocking CI, patching a CVE, removing a broken feature flag

## Dashboard Metrics

Track these over time to measure debt trajectory:

| Metric                  | Target          | Signal                              |
|-------------------------|-----------------|-------------------------------------|
| Total debt items        | Decreasing      | Overall debt load                   |
| New debt / sprint       | < Resolved debt | Are we creating more than we fix?   |
| Age of oldest item      | < 6 months      | Are items getting stuck?            |
| Quick wins remaining    | 0               | Low-hanging fruit should not linger |
| Strategic items planned | >= 1 / quarter  | Are we investing in big fixes?      |
| Interest rate HIGH count| Decreasing      | Compounding debt is most dangerous  |

## Debt Inventory Template

```
ID: DEBT-042
Type: Design
Signal: Circular dependency between UserService and AuthService
Interest rate: HIGH (every new auth feature deepens the cycle)
Blast radius: HIGH (affects all authenticated endpoints)
Fix cost now: 3 days | Fix cost in 6 months: 2 weeks
Priority: STRATEGIC
Recommendation: Extract shared types to a contracts module
```
