---
title: Receiving Code Review
impact: HIGH
impactDescription: Reacting defensively or complying performatively to review feedback wastes the reviewer's time and hides real issues
tags: code-review, receiving, feedback, pushback, collaboration
---

# Receiving Code Review

Most code review guidance teaches how to *give* reviews. This covers how to
*receive* them -- evaluate feedback technically, push back when warranted,
and avoid performative compliance.

## Workflow

When you receive review feedback (from a human reviewer or an agent):

### 1. Restate the concern

Before responding, restate the reviewer's concern in your own words. This
catches misunderstandings before they become wasted work.

```
Reviewer: "This function does too much."
You: "You're saying process_order() has too many responsibilities --
      validation, pricing, and notification should be separate concerns?"
```

If you cannot restate it, ask for clarification. Do not guess.

### 2. Verify the claim

Check whether the feedback is factually correct before acting on it:

- **Does the cited code actually behave as described?** Read it.
- **Does the suggested alternative actually work?** Trace the edge cases.
- **Is the concern about this PR, or about pre-existing code?** If the
  reviewer is asking you to fix pre-existing issues, that is scope creep
  unless it is directly related to your change.

### 3. Evaluate the trade-off

Not all valid feedback requires action. Evaluate:

- **Severity:** Does this cause bugs, security holes, or data loss? Fix it.
  Is it a style preference? Discuss it.
- **Blast radius:** Does the suggested change affect only this PR, or does
  it require changes across the codebase? If the latter, file a follow-up
  rather than expanding this PR.
- **Consistency:** Is the reviewer asking you to follow a pattern that
  exists elsewhere in the codebase? Follow it. Are they asking you to
  pioneer a new pattern? Push back unless there is consensus.

### 4. Respond technically

Three valid responses to review feedback:

**Agree and fix:**
```
"Good catch -- the nil case is unhandled. Fixed in abc123."
```

**Agree but defer:**
```
"Valid concern. This is pre-existing -- I've filed #456 to address it
separately so this PR stays focused."
```

**Disagree with reasoning:**
```
"I considered extracting this, but the two callers use it differently
enough that a shared abstraction would be leaky. Keeping them inline
avoids coupling them. Happy to discuss if you see a clean boundary."
```

### 5. Implement and verify

After making changes from review feedback:

1. Run the full test suite (not just the tests you think are affected)
2. Re-read the reviewer's original comment to confirm you addressed the
   actual concern, not a reinterpretation of it
3. Link the fixing commit in your response

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| **Performative compliance** | Changing code without understanding why, just to close the comment | Restate the concern first. If you cannot explain why the change is better, ask. |
| **Defensive dismissal** | "It works fine" without engaging with the technical concern | Engage with the specific claim. Trace the scenario the reviewer described. |
| **Scope explosion** | Accepting all suggestions, turning a focused PR into a refactoring marathon | Agree-and-defer for anything outside the PR's original scope. |
| **Silent changes** | Making review-driven changes without explaining what you did or why | Link the commit. State what you changed and how it addresses the concern. |
| **Authority appeal** | "The senior dev told me to do it this way" | Explain the technical reasoning, not who said it. |
