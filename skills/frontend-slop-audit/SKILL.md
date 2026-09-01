---
name: frontend-slop-audit
description: >
  Audit generated web UI for AI-generated tells and ship-blocking layout defects.
  TRIGGER when: reviewing a landing page, portfolio, or marketing site before shipping;
  user asks why a page "looks AI-generated", "looks templated", or "looks generic";
  or asks for an anti-slop pass, taste pass, or pre-flight check on frontend output.
  DO NOT TRIGGER when: making design-system decisions such as tokens, palettes, type
  scales, or motion architecture (use design-ux skill), reviewing code correctness or
  security (use code-review skill), generating favicons or social images (use
  web-asset-generator skill), or working on terminal/TUI interfaces (use design-ux skill).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: audit, frontend, ui, review, anti-slop, landing-page, pre-flight, taste
---

# frontend-slop-audit

Audit an already-built page for the patterns that mark it as machine-generated. This is a review pass, not a design pass: it takes existing output and returns a list of specific, located defects.

Two kinds of finding. **Hard rules** are countable or measurable -- a wrapped CTA, a two-line nav, five eyebrows across seven sections -- and failing one means the page is broken, not merely unfashionable. **Tells** are patterns that are individually defensible but appear so reliably in generated output that their presence identifies the author. Both are empirical, mined from repeated production failures rather than derived from principle, which is also why they need re-verification over time.

## What You Get

- A catalog of AI-generated visual, copy, and structural tells with concrete replacements
- Mechanically checkable layout rules (hero fit, eyebrow ratio, bento cell count, CTA discipline)
- An 8-group pre-flight checklist ordered cheapest-check-first
- Contrast and consistency-lock verification steps that catch defects static review misses
- A reporting format that produces located, actionable findings

## When to Use

- Auditing a generated landing page, portfolio, or marketing site before shipping
- Diagnosing why a page "looks AI-generated" or "looks templated"
- Running a final pre-flight pass over frontend output
- Reviewing a redesign against the page it replaced
- Establishing ship criteria for machine-generated UI

## When NOT to Use

- **Design decisions** (tokens, palettes, type scales, grids, motion architecture) -- use `design-ux`
- **Code correctness, security, blast radius** -- use `code-review`
- **Favicons, OG images, icon sets** -- use `web-asset-generator`
- **Terminal and TUI interfaces** -- use `design-ux`, which owns the monospace side
- **Dashboards, data tables, multi-step forms** -- these rules target marketing and portfolio surfaces; product UI has different density constraints

## Reading Guide

| Working on                                      | Read                     |
| ----------------------------------------------- | ------------------------ |
| Running the audit end to end                    | `pre-flight-check.md`    |
| Visual, copy, and decoration tells              | `ai-tells.md`            |
| Countable layout defects, hero, nav, CTA, contrast | `layout-hard-rules.md` |

## See also

- `design-ux` -- for the design decisions this skill audits against
- `code-review` -- for correctness, security, and blast radius
- `web-asset-generator` -- for producing the favicons and social images this skill expects to exist
- `playwright` -- for driving the page to verify rendered contrast and viewport behavior

## Common Pitfalls

| Mistake                              | Why It Fails                                          | Better Approach                                      |
| ------------------------------------ | ----------------------------------------------------- | ---------------------------------------------------- |
| Reporting a pass/fail verdict        | Gives the author nothing to act on                    | Report each failure with file, line, and fix         |
| Listing rules that passed            | Buries the findings in noise                          | Report only failures                                 |
| Treating tells as universal law      | These are 2026 defaults, not design truths            | Re-verify annually; drop entries that stop being defaults |
| Applying marketing rules to product UI | Density constraints are genuinely different          | Scope the audit to marketing and portfolio surfaces  |
| Assuming contrast from token names   | `bg-white` plus `text-white` both look intentional    | Check computed values against the rendered background |
| Rewriting the page                   | The ask is an audit, not a redesign                   | Return findings; let the author decide the fix       |
| Flagging every em-dash in source     | The rule is about rendered page text                  | Check visible strings, not code comments             |

## Key Conventions

- **Countable before subjective**: run the mechanical checks first; they need no judgment and catch the most
- **Located findings only**: a rule cited without a line number is not a finding
- **Empirical, not eternal**: every tell carries a date stamp and an expiry expectation
- **Audit, do not redesign**: this skill returns a defect list, not new markup
- **Static is a valid outcome**: a page with no motion passes the motion group; half-built motion does not

## Attribution

The tell catalog, layout rules, and checklist are adapted from [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) (MIT, upstream commit `ccbc156`), restructured for progressive disclosure and scoped to the audit job. Full notice in `THIRD-PARTY-NOTICES.md` at the repository root.
