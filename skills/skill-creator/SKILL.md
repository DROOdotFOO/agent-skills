---
name: skill-creator
description: >
  Interactively scaffold new Claude Code skills with correct frontmatter,
  trigger clauses, sub-files, and linter compliance. TRIGGER when: user asks
  to create a new skill, scaffold a skill, add a skill to agent-skills, or
  says "new skill" or "skill creator". DO NOT TRIGGER when: user is editing
  an existing skill, writing CLAUDE.md instructions, or building an MCP
  server (use mcp-server-builder skill).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: skill, scaffold, creator, template, claude-code, meta
---

# Skill Creator

Scaffold new Claude Code skills that pass `./scripts/skills-lint.sh` on the
first try. Walk the user through naming, trigger design, sub-file structure,
and quality review.

## What is a skill?

A skill is a directory under `skills/<name>/` containing markdown files with
YAML frontmatter. The entry point is always `SKILL.md`. Skills provide
context-injection for Claude Code sessions -- they load automatically when
trigger conditions in the description match the user's task.

Skills are NOT agents, NOT plugins, NOT code libraries. They are structured
knowledge documents that shape Claude's behavior for a specific domain.

## Scaffolding workflow

### Step 1: Choose a name

- Lowercase, hyphenated: `my-skill-name`
- Short but specific: prefer `database-designer` over `db` or `database-schema-design-and-optimization-tool`
- Check for overlap with existing skills before creating

### Step 2: Write trigger clauses

The description field in SKILL.md frontmatter MUST include both:

- **TRIGGER when:** -- enumerate concrete conditions (imports, file types, user phrases)
- **DO NOT TRIGGER when:** -- exclude adjacent domains to prevent false activation

Good triggers are specific and observable:

```
TRIGGER when: user asks to design a REST API, define endpoint schemas,
or working with OpenAPI spec files (.yaml/.json with openapi: field).
DO NOT TRIGGER when: user is implementing API handlers (use the
language-specific skill), or configuring an API gateway.
```

Bad triggers are vague:

```
TRIGGER when: user is working with APIs.
```

### Step 3: Write SKILL.md body

After the frontmatter, structure the body:

1. **One-paragraph summary** -- what the skill does, when to use it
2. **Workflow or phases** -- the step-by-step process the skill guides
3. **Key rules or checklists** -- what to always/never do
4. **Common pitfalls** -- table of mistake/fix pairs
5. **Reading guide** -- table linking to sub-files with backtick-wrapped paths

### Step 4: Create sub-files

Each sub-file covers one focused topic. Every sub-file needs YAML frontmatter
with three required fields:

- `impact`: one of `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
- `impactDescription`: one sentence explaining why this matters
- `tags`: comma-separated string (NOT a YAML array)

Sub-files should contain **incorrect/correct example pairs** showing what to
do and what not to do, with brief explanations.

### Step 5: Validate

```bash
./scripts/skills-lint.sh
```

The linter checks:
- SKILL.md exists with `name:`, `description:`, `metadata:` fields
- Description contains `TRIGGER when:` and `DO NOT TRIGGER`
- Sub-files have YAML frontmatter with `impact` and `impactDescription`
- Tags are comma-separated strings, not YAML arrays
- File references in reading guide tables point to real files
- Cross-skill references in "See also" point to real skill directories

## What You Get

- A complete `skills/<name>/` directory with a SKILL.md entry point containing valid frontmatter and trigger clauses
- Sub-files with correct YAML frontmatter (impact, impactDescription, tags) and incorrect/correct example pairs
- A skill that passes `./scripts/skills-lint.sh` on the first run with no manual fixes needed

## Reading guide

| Topic | File |
| --- | --- |
| Copy-paste frontmatter templates for SKILL.md and sub-files | `templates.md` |
| Quality checklist, anti-patterns, review criteria | `quality-checklist.md` |

## See also

- `codebase-onboarding`
- `architect`
