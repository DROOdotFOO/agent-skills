---
name: ubiquitous-language
description: >
  Extract and maintain a DDD ubiquitous language glossary from conversations.
  TRIGGER when: user asks to define domain terms, extract a glossary, build a
  ubiquitous language, or says "ubiquitous language". Also when domain
  ambiguity, synonym conflicts, or overloaded terms appear in conversation.
  DO NOT TRIGGER when: user wants code review, API docs, or module naming
  conventions (those are implementation, not domain).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: ddd, domain-driven-design, glossary, ubiquitous-language, terminology
---

# ubiquitous-language

Extract canonical domain terminology from conversations. Be opinionated.
Flag ambiguity. Pick winners. Write `UBIQUITOUS_LANGUAGE.md`.

## Process

1. **Scan** -- Read the conversation (or codebase) for domain-specific terms
2. **Identify problems** -- Flag: ambiguous terms, synonyms used interchangeably,
   overloaded terms (same word, different meanings in different contexts),
   terms with no clear definition
3. **Propose canonical glossary** -- Pick one term per concept. Be opinionated.
   If two terms compete, choose the more precise one and list the loser as
   an alias to avoid
4. **Write file** -- Output `UBIQUITOUS_LANGUAGE.md` in the project root
5. **Merge on re-run** -- If the file exists, merge new terms into existing
   tables. Flag conflicts between old and new definitions

## Output Format

Group terms into multiple tables by domain area (not one giant table).

```markdown
## [Domain Area Name]

| Term   | Definition                                | Aliases to avoid      |
| ------ | ----------------------------------------- | --------------------- |
| Ledger | Append-only record of all balance changes | log, journal, history |

### Relationships

- A Ledger contains many Entries (1:N)
- Each Entry references exactly one Account (N:1)

### Example dialogue

> "When a user transfers funds, a new Entry is appended to the Ledger."
> NOT: "When a user moves money, a new log item is added to the history."

### Flagged ambiguities

- "Account" -- used to mean both user identity and financial account.
  DECISION: use "Account" for financial, "User" for identity.
```

## What You Get

- A `UBIQUITOUS_LANGUAGE.md` file in the project root with canonical terms grouped by domain area
- Tables listing each term's definition, aliases to avoid, relationships with cardinality, and example dialogue
- Flagged ambiguities where the same word means different things in different contexts, each with a documented decision

## Rules

1. **Be opinionated** -- Pick one canonical term per concept, always
2. **Flag conflicts** -- If the conversation uses two terms for one concept,
   call it out explicitly and choose a winner
3. **Domain terms only** -- Exclude module names, class names, function names,
   and implementation details. Capture the business/problem-space language
4. **Tight definitions** -- One sentence max. If you need two, split the concept
5. **Show relationships** -- Include cardinality (1:1, 1:N, N:N)
6. **Group into tables** -- One table per domain area, not one flat list
7. **Include example dialogue** -- Show how the term should be used in conversation
8. **Merge, don't replace** -- Re-running adds new terms and flags conflicts
   with existing definitions
