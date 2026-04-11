---
title: Readiness Checklist
impact: CRITICAL
impactDescription: Releasing without validation causes production incidents and customer-facing breakage
tags: release,checklist,dora-metrics,rollback,hotfix,validation
---

# Readiness Checklist

Pre-release validation, incident response procedures, and deployment health metrics.

## Pre-release Checks

Run all checks before tagging a release. Each must pass or have an explicit waiver with justification.

### Code Quality

- [ ] All CI checks pass on the release branch (no flaky test waivers)
- [ ] No critical or high severity vulnerabilities (`npm audit`, `cargo audit`, `mix audit`, `pip-audit`)
- [ ] No compiler warnings treated as errors
- [ ] Linter passes with zero warnings on changed files

### Versioning

- [ ] Version bumped in all required files (package.json, mix.exs, Cargo.toml, pyproject.toml)
- [ ] Version follows SemVer rules based on commit analysis
- [ ] No version conflicts in lock files

### Documentation

- [ ] CHANGELOG.md updated with all user-facing changes
- [ ] Breaking changes include migration guide or action items
- [ ] API documentation reflects new/changed endpoints
- [ ] README updated if setup steps changed

### Testing

- [ ] All tests pass (unit, integration, e2e)
- [ ] New features have test coverage
- [ ] Breaking changes have migration test or upgrade test
- [ ] Performance benchmarks show no regression (if applicable)

### Stakeholder

- [ ] Release notes reviewed by product/team lead
- [ ] Breaking changes communicated to downstream consumers
- [ ] Release timing avoids freeze periods and high-traffic windows

## DORA Metrics

Track these four metrics to measure release health over time:

| Metric                | Elite        | High          | Medium        | Low            |
|-----------------------|--------------|---------------|---------------|----------------|
| Lead time for changes | < 1 hour     | 1 day - 1 week| 1 week - 1 month| > 1 month    |
| Deploy frequency      | On demand    | Daily - weekly| Weekly - monthly| Monthly+     |
| MTTR                  | < 1 hour     | < 1 day       | < 1 week      | > 1 week       |
| Change failure rate   | < 5%         | 5-10%         | 10-15%        | > 15%          |

Use these to identify systemic release process problems, not to judge individual releases.

## Hotfix Procedures

When a release causes production issues, classify and respond by severity:

### P0 -- Critical (SLA: fix in 1 hour)

- Data loss, security breach, complete service outage
- Immediate rollback, then root cause analysis
- All hands on deck, stakeholder notification within 15 minutes
- Post-incident review required within 48 hours

### P1 -- Major (SLA: fix in 4 hours)

- Feature broken for all users, significant performance degradation
- Hotfix branch from release tag, expedited review (1 reviewer)
- Stakeholder notification within 1 hour

### P2 -- Minor (SLA: fix in 1 business day)

- Feature broken for subset of users, cosmetic issues with workaround
- Normal PR process with priority label
- Include fix in next scheduled release if possible

## Rollback Planning

Every release must have a rollback plan before deployment:

1. **Identify rollback method** -- Git revert, feature flag toggle, infrastructure rollback (Kubernetes rollout undo, blue-green switch)
2. **Database compatibility** -- Can the previous version run against the new schema? If migrations are destructive, rollback requires a data fix.
3. **Test rollback** -- In staging, deploy the new version, then roll back. Verify the service recovers.
4. **Document the command** -- Write the exact rollback command in the release notes.

```
Rollback plan:
  Method: git revert + redeploy
  DB compatible: yes (additive migration only)
  Command: git revert v3.0.0..HEAD && git push && deploy
  Verified in staging: yes
```
