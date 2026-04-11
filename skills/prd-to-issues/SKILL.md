---
name: prd-to-issues
description: >
  Convert a PRD into GitHub issues with HITL/AFK classification, in dependency order.
  TRIGGER when: user asks to break a PRD into issues, create issues from a plan,
  convert requirements to GitHub issues, or says "prd to issues".
  DO NOT TRIGGER when: user asks to write a PRD, review a plan, or create a single issue.
metadata:
  author: mattpocock
  version: "1.0.0"
  tags: prd, github, issues, planning, hitl, afk, vertical-slices
  license: MIT
---

# PRD to Issues

Convert a Product Requirements Document into a set of GitHub issues, each tagged
as HITL (human-in-the-loop) or AFK (autonomous), created in dependency order.

## What You Get

- Vertical-slice issues derived from a PRD
- HITL/AFK classification on every issue (see `hitl-vs-afk.md`)
- Dependency ordering -- blockers created first, dependents reference real issue numbers
- Consistent issue format with acceptance criteria (see `issue-template.md`)
- Parent PRD is referenced but never modified

## Workflow

1. **Locate the PRD.** Accept a file path, paste, or GitHub issue URL. If given an
   issue URL or number, fetch it with `gh issue view <number> --json body,title`.
2. **Explore the codebase.** Understand the existing architecture, conventions,
   and test patterns before slicing.
3. **Draft vertical slices.** Each slice is an independently-grabbable unit of work.
   Tag every slice HITL or AFK. Default to AFK -- escalate to HITL only when
   criteria from `hitl-vs-afk.md` are met.
4. **Quiz the user.** Present the proposed breakdown. Ask one question at a time
   about any slice where scope or classification is uncertain. Adjust based on
   answers.
5. **Create issues.** Use `gh issue create` in dependency order so that
   `blocked-by` references use real issue numbers. Blockers are created first.

## Rules

1. **Vertical slices only.** Each issue must be independently implementable and
   deliver a testable increment. No "set up infrastructure" issues that deliver
   nothing visible.
2. **Prefer AFK.** Default every issue to AFK. Only escalate to HITL when the
   criteria in `hitl-vs-afk.md` clearly apply.
3. **Dependency order.** Create blocking issues first. Dependent issues reference
   the real `#number` of their blockers.
4. **Do not modify the PRD.** The parent PRD issue stays open and unedited.
   Issues reference it; they do not close or update it.
5. **One issue per slice.** Do not combine multiple slices into a single issue.
   Do not split a single slice across multiple issues.
6. **Acceptance criteria are checkboxes.** Every issue has concrete, testable
   acceptance criteria as a markdown checkbox list.
7. **Ask before creating.** Always present the full breakdown and get user
   approval before running any `gh issue create` commands.

## Quick Reference

| Classification | Meaning | Default? |
|----------------|---------|----------|
| AFK | Can be implemented and merged autonomously | Yes |
| HITL | Needs human decision, review, or input | No -- must justify |

See `hitl-vs-afk.md` for classification details and `issue-template.md` for the
issue body format.
