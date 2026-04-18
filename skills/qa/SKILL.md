---
name: qa
description: >
  Interactive QA session with background codebase exploration. User reports
  bugs conversationally, agent explores context via sub-agents, assesses
  scope, and files issues via gh. TRIGGER when: user wants to report bugs,
  run a QA session, do bug triage, or says "qa session". DO NOT TRIGGER when:
  user wants to fix a bug (use focused-fix), or wants a code review of a PR
  (use code-review).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: qa, bugs, issues, triage, github, testing
---

# qa

Interactive QA session. User talks about bugs. Agent explores the codebase
in the background, assesses scope, and files clean issues via `gh`.

## Workflow (per issue)

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

## Rules

1. **No file paths in issues** -- Describe the problem in domain language,
   not implementation details. Developers will find the code
2. **Use project domain language** -- Match the terminology of the project,
   not generic tech jargon
3. **Describe behaviors, not code** -- "Login fails when email has a plus sign"
   not "validateEmail regex doesn't match + character"
4. **Reproduction steps are mandatory** -- Every issue must have steps to
   reproduce, even if inferred from the conversation
5. **Keep concise** -- Issues should be scannable in 30 seconds

## Single issue template

```
gh issue create --title "SHORT DESCRIPTION" --body "$(cat <<'EOF'
## Bug

[One sentence description of the incorrect behavior]

## Expected behavior

[What should happen instead]

## Steps to reproduce

1. [Step]
2. [Step]
3. [Observe: incorrect behavior]

## Notes

[Any additional context from exploration, e.g., "This may be related to #42"]
EOF
)"
```

## What You Get

- One or more GitHub issues filed via `gh issue create`, each with reproduction steps, expected behavior, and exploration notes
- Parent/child issue trees when a single report reveals multiple distinct bugs
- A running QA session log -- return to it with "what else?" until you say done

## Breakdown template

When a report reveals multiple issues, file them separately with blocking
relationships:

```
gh issue create --title "PARENT: short description" --body "..."
# Then for each sub-issue:
gh issue create --title "SUB: specific problem" --body "Blocked by #PARENT_NUM ..."
```

Label the parent issue with the list of sub-issues. Each sub-issue references
the parent. Fix order flows from dependencies, not from severity.
