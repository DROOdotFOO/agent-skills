---
title: Frontmatter Templates
impact: CRITICAL
impactDescription: Wrong frontmatter causes linter failures and prevents skill activation
tags: template, frontmatter, yaml, scaffold
---

# Frontmatter Templates

Copy-paste these templates when creating new skills. Every field shown is
required unless marked optional.

## SKILL.md frontmatter

```yaml
---
name: my-skill-name
description: >
  One-sentence summary of what this skill does. TRIGGER when: user asks
  about X, works with Y files, imports Z modules, or says "phrase".
  DO NOT TRIGGER when: user is doing adjacent-thing (use other-skill).
metadata:
  author: YourName
  version: "1.0.0"
  tags: tag1, tag2, tag3, relevant-domain
---
```

### Field rules

| Field | Type | Rules |
| --- | --- | --- |
| `name` | string | Must match the directory name exactly |
| `description` | string | Use `>` for folded scalar. Must contain `TRIGGER when:` and `DO NOT TRIGGER` |
| `metadata.author` | string | Who created the skill |
| `metadata.version` | string | Quoted semver (YAML treats bare `1.0` as float) |
| `metadata.tags` | string | Comma-separated, lowercase, no brackets |

### Description patterns

**Single-domain skill** (most common):

```yaml
description: >
  Schema analysis and migration safety for relational databases.
  TRIGGER when: user asks about database schema design, normalization,
  index strategy, or migration planning.
  DO NOT TRIGGER when: user is querying data (not designing schema),
  or working with NoSQL/document stores.
```

**Multi-signal skill** (triggers on files, imports, and phrases):

```yaml
description: >
  Solidity development standards and security auditing.
  TRIGGER when: working with .sol files, foundry.toml,
  hardhat.config.*, smart contract auditing, or security review.
  DO NOT TRIGGER when: deploying contracts (use deployment skill),
  or working with non-EVM chains.
```

## Sub-file frontmatter

```yaml
---
title: Descriptive Title
impact: HIGH
impactDescription: One sentence on why getting this wrong matters
tags: tag1, tag2, specific-topic
---
```

### Impact levels

| Level | When to use | Example |
| --- | --- | --- |
| `CRITICAL` | Getting this wrong breaks the skill or causes security issues | Auth patterns, frontmatter format |
| `HIGH` | Getting this wrong produces poor results most of the time | Trigger clause design, example quality |
| `MEDIUM` | Getting this wrong degrades quality in some cases | File organization, naming conventions |
| `LOW` | Nice to have, minor polish | Formatting preferences, optional metadata |

### Tags format

CORRECT -- comma-separated string:

```yaml
tags: testing, patterns, polyglot
```

WRONG -- YAML array (linter will reject this):

```yaml
tags: [testing, patterns, polyglot]
```

WRONG -- YAML list:

```yaml
tags:
  - testing
  - patterns
```

## Persona primer (optional)

For skills that model expert behavior, add a one-line persona blockquote
immediately after the frontmatter closing `---`, before the first heading.
This frames the LLM's role and quality bar for the entire skill.

```markdown
> **You are a [Role Title]** -- [one sentence framing expertise and judgment style].
```

Examples:

```markdown
> **You are a Principal Application Security Engineer** -- you think in attack surfaces, not feature lists, and you never sign off without verifying the fix.
```

```markdown
> **You are a Staff Performance Engineer** -- you never optimize without a flamegraph, and you distrust any claim that lacks before/after numbers.
```

Good persona primers are **opinionated** (state what this expert values and distrusts)
rather than generic ("you are an expert who writes good code").

## SKILL.md body structure

After frontmatter (and optional persona primer), follow this skeleton:

```markdown
# Skill Name

One paragraph: what it does, who it's for, when to reach for it.

## Workflow (or Phases, or Core Rules)

The main content. Numbered steps, checklists, decision trees.

## Common Pitfalls

| Mistake | Fix |
| --- | --- |
| Overly broad triggers | Add specific file/import/phrase signals |
| No examples | Add incorrect/correct pairs in sub-files |

## Reading guide

| Topic | File |
| --- | --- |
| Description of topic | `filename.md` |

## See also

- `related-skill-name`
```

The reading guide table MUST use backtick-wrapped filenames that point to
real files in the skill directory. The linter checks this.

The "See also" section MUST reference skill directory names that exist under
`skills/`. The linter checks this too.
