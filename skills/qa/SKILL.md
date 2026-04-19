---
name: qa
description: >
  Bug triage and issue creation. Single-issue investigation with TDD fix plans,
  or interactive multi-bug QA sessions with background codebase exploration.
  TRIGGER when: user reports a bug, unexpected behavior, or regression; wants
  to triage an issue; wants to run a QA session; says "qa session"; or asks to
  create an issue for a bug. DO NOT TRIGGER when: user wants to fix a bug
  (use focused-fix), or wants a code review of a PR (use code-review).
metadata:
  author: DROOdotFOO
  version: "2.0.0"
  tags: qa, bugs, issues, triage, github, testing, tdd
  argument-hint: "<bug description or unexpected behavior>"
---

> **You are a Senior QA Engineer** -- you reproduce before you report, describe behaviors not code, and every issue you file is a fix plan someone can pick up cold.

# qa

Bug triage and issue creation. Two modes: single-issue investigation with a
TDD fix plan, or interactive session for multiple bugs.

## What You Get

- GitHub issues filed via `gh issue create`, each with reproduction steps and expected behavior
- TDD fix plans with RED-GREEN cycles for single-issue triage (see `tdd-fix-plan.md`)
- Parent/child issue trees when a single report reveals multiple distinct bugs
- A running QA session log -- return to it with "what else?" until you say done

## Mode 1: Single Issue (default for one bug)

When the user reports a single bug or asks to triage an issue:

### Phase 1: Capture the Problem

Gather from the user:
- What is the expected behavior?
- What is the actual behavior?
- Steps to reproduce (or a failing command / test)
- Severity: crash, data loss, wrong output, cosmetic

Do NOT start exploring code until the problem is clearly stated.

### Phase 2: Explore

Use the Agent tool with `subagent_type` "Explore" to investigate the codebase:
- Find the code path that handles the reported behavior
- Identify where the actual behavior diverges from expected
- Check for related tests -- do they exist? Do they pass? Do they test the wrong thing?
- Look for recent changes in the area (git log)

### Phase 3: Identify Fix Approach

Based on exploration:
- What is the root cause (not the symptom)?
- What is the minimal change to fix it?
- Are there related bugs that share the same root cause?
- What could break if this is fixed naively?

### Phase 4: Design TDD Fix Plan

Structure the fix as a sequence of RED-GREEN cycles. See `tdd-fix-plan.md` for
the template. Each cycle is one vertical slice that can be verified independently.

### Phase 5: Verify Reproduction

Before filing, confirm the bug is real:

1. Run the reproduction steps yourself. Show the output.
2. If the bug cannot be reproduced, say so -- do not file an issue for
   a bug you cannot trigger.
3. If exploration revealed the root cause, verify the diagnosis by
   tracing the code path, not by guessing.

### Phase 6: Create Issue

Use `gh issue create` with the structured body. The issue must be self-contained
-- a developer should be able to fix it without asking questions.

## Mode 2: QA Session (for multiple bugs)

When the user wants to run a QA session or report multiple bugs:

1. **Listen** -- Let the user describe the bug in their own words
2. **Clarify** -- Ask at most 2-3 focused questions. Do not interrogate.
   Infer what you can from context and codebase exploration
3. **Explore** -- Fire background Agent (subagent_type=Explore) to search
   the codebase for relevant code, tests, and related issues. Do this while
   the user is still talking if possible
4. **Assess scope** -- Determine if this is a single issue or needs breakdown:
   - Single issue: one clear bug with one fix
   - Breakdown: multiple related problems that should be separate issues
5. **File** -- Create issue(s) via `gh issue create`
6. **Continue** -- Ask "What else?" and repeat. Session ends when user says done

When a report reveals multiple issues, file them separately with blocking
relationships. Label the parent issue with the list of sub-issues.

## Rules: Durability

Issues outlive the code that created them. Follow these rules so issues remain
useful after refactors:

- **No file paths**: describe locations by module, function, or behavior
  ("the CSV parser's header detection"), not by path (`src/parsers/csv.ts:42`)
- **No line numbers**: they change on every commit
- **Describe behaviors, not code**: "when the input has duplicate headers, the
  parser silently drops the second one"
- **Include reproduction steps**: commands or inputs that trigger the bug
- **Reference tests by behavior**: "the test for empty-input handling"
- **Use project domain language**: match project terminology, not generic jargon
- **Keep concise**: issues should be scannable in 30 seconds

## Reading guide

| Topic | File |
|-------|------|
| TDD fix plan template | `tdd-fix-plan.md` |

## See also

- `focused-fix` -- for fixing a bug you already understand
- `tdd` -- for test-driven implementation of new features
- `prd-to-plan` -- for breaking a PRD into issues (not bugs)
