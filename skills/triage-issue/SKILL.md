---
name: triage-issue
description: |
  Bug investigation workflow that produces a GitHub issue with a TDD fix plan.
  TRIGGER when: user reports a bug, unexpected behavior, or regression and wants it triaged, or asks to create an issue for a bug.
  DO NOT TRIGGER when: user already has an issue and wants to fix it, or is writing tests for known behavior.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: triage, bugs, github, issues, tdd, investigation
---

# Triage Issue

## Philosophy

A good bug report is a fix plan. Capture the problem, explore the codebase to understand root cause, then write an issue that a developer (or future agent) can pick up and fix using TDD -- without needing to re-investigate.

## Workflow: 5 Phases

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

Structure the fix as a sequence of RED-GREEN cycles. See [tdd-fix-plan.md](tdd-fix-plan.md) for the template. Each cycle is one vertical slice that can be verified independently.

### Phase 5: Create Issue

Use `gh issue create` with the structured body. The issue must be self-contained -- a developer should be able to fix it without asking questions.

## Rules: Durability

Issues outlive the code that created them. Follow these rules so issues remain useful after refactors:

- **No file paths**: describe locations by module, function, or behavior ("the CSV parser's header detection"), not by path (`src/parsers/csv.ts:42`).
- **No line numbers**: they change on every commit.
- **Describe behaviors, not code**: "when the input has duplicate headers, the parser silently drops the second one" -- not "the for loop on line 42 skips duplicates."
- **Include reproduction steps**: commands or inputs that trigger the bug, not "see the code."
- **Reference tests by behavior**: "the test for empty-input handling" -- not "test_csv_empty in test_parsers.py."

## Sub-files

| File | Topic |
|------|-------|
| [tdd-fix-plan.md](tdd-fix-plan.md) | RED-GREEN cycle structure for issue body |
