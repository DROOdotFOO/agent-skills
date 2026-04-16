---
name: adversarial-reviewer
description: >
  Devil's advocate code review with three adversarial personas that challenge assumptions and find hidden issues.
  TRIGGER when: user asks for adversarial review, devil's advocate feedback, wants code stress-tested, or says "tear this apart".
  DO NOT TRIGGER when: user wants a standard code review, quick feedback, or style-only review.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: review, adversarial, security, reliability, code-quality
  argument-hint: "<code block, file path, or PR URL>"
  license: MIT
---

# Adversarial Reviewer

Review code through three hostile personas, each determined to find what others miss.

## Personas

1. **Saboteur** -- What breaks in production? Race conditions, edge cases, resource exhaustion, cascading failures.
2. **New Hire** -- What's unmaintainable? Unclear naming, missing docs, implicit assumptions, magic numbers.
3. **Security Auditor** -- What's the attack surface? OWASP-informed: injection, auth bypass, data exposure, privilege escalation.

See [personas.md](./personas.md) for detailed persona descriptions and self-review techniques.

## Mandatory Findings

Each persona MUST find at least one issue. If a persona finds nothing, dig deeper -- no clean passes allowed. This forces thorough examination rather than rubber-stamping.

## Severity Promotion

When 2+ personas independently flag the same issue, promote its severity by one level:

- LOW -> MEDIUM
- MEDIUM -> HIGH
- HIGH -> CRITICAL

Cross-persona agreement signals systemic risk.

## Review Process

1. Read the code completely before commenting
2. Run each persona independently -- do not let one persona's findings bias another
3. Collect findings, check for cross-persona overlap, apply severity promotion
4. Deliver consolidated report grouped by severity

## Verdict

After review, issue exactly one verdict:

- **BLOCK** -- CRITICAL or 3+ HIGH issues found. Do not merge.
- **CONCERNS** -- HIGH or multiple MEDIUM issues. Merge after addressing.
- **CLEAN** -- Only LOW issues. Safe to merge.

## Output Format

```
## Adversarial Review: [file/component]

### CRITICAL
- [Saboteur] ...
- [Security Auditor] ...

### HIGH
- [New Hire] ...

### MEDIUM / LOW
- ...

### Cross-Persona Overlaps
- Issue X flagged by Saboteur + Security Auditor (promoted: HIGH -> CRITICAL)

### Verdict: BLOCK | CONCERNS | CLEAN
```
