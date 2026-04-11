---
name: codebase-onboarding
description: >
  Auto-generate onboarding documentation from codebase analysis, tailored
  to the reader's experience level. TRIGGER when: user asks to onboard someone
  to a codebase, generate project documentation for new team members, create
  a getting-started guide, or explain a codebase to a specific audience.
  DO NOT TRIGGER when: user wants API reference docs (use language-specific
  tooling), or wants to understand a single file (just read it).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: onboarding, documentation, architecture, codebase-analysis, team
---

# codebase-onboarding

Auto-generate onboarding documentation from codebase analysis. Audience-aware
output for junior developers, senior engineers, and contractors.

## What You Get

- Architecture overview derived from actual code structure
- Key entry points and control flow
- Testing strategy and deployment process
- Domain glossary extracted from code and comments
- Audience-tailored depth and focus

## Workflow

1. **Analyze** -- Scan the codebase to discover stack, structure, and patterns
2. **Capture signals** -- Identify entry points, config files, CI/CD, test
   patterns, dependency graph, domain terms
3. **Fill template** -- Populate the output format sections below
4. **Tailor** -- Adjust depth and emphasis for the target audience

## Analysis signals

Scan for these to build the onboarding doc:

| Signal             | Where to look                                      |
| ------------------ | -------------------------------------------------- |
| Language/framework  | package.json, mix.exs, go.mod, Cargo.toml, pyproject.toml |
| Entry points       | main files, router definitions, CLI entry points   |
| Config             | .env.example, config/, settings files              |
| CI/CD              | .github/workflows/, Makefile, Dockerfile           |
| Tests              | test/, spec/, __tests__/, *_test.go                |
| Database           | migrations/, schema files, ORM models              |
| API surface        | OpenAPI specs, GraphQL schema, route definitions   |
| Domain terms       | README, doc comments, module names, type names     |
| Dependencies       | Lock files, vendor/, package manifests             |
| Dev setup          | Makefile, docker-compose.yml, devcontainer.json    |

## Audience descriptions

### Junior developer

**Focus**: Setup, guardrails, where to look first.

Include: step-by-step local setup, "your first task" walkthrough, which files
NOT to touch, who to ask for help, common gotchas, link to style guide.
Omit: architecture rationale, ops runbooks, deployment internals.

### Senior engineer

**Focus**: Architecture, operations, decision rationale.

Include: system architecture diagram, data flow, tech debt inventory,
performance characteristics, deployment pipeline, on-call procedures,
ADRs (or why decisions were made if no ADRs exist).
Omit: basic setup steps, language tutorials, tool installation.

### Contractor

**Focus**: Scoped ownership, boundaries, escalation paths.

Include: which modules they own, integration boundaries (what they can
and cannot change), PR review process, communication channels, access
provisioning checklist, contract-relevant SLAs.
Omit: long-term roadmap, internal politics, systems outside their scope.

## Output format

Generate a document with these sections (skip any that are not applicable):

```markdown
# [Project Name] Onboarding Guide
> Audience: [Junior / Senior / Contractor]
> Generated: [date]

## Architecture overview
[High-level diagram or description of major components and their relationships]

## Key entry points
[Where execution starts, main routes/handlers, CLI commands]

## Local development setup
[Prerequisites, clone, install, run, verify]

## Testing strategy
[How to run tests, what frameworks are used, coverage expectations]

## Deployment process
[How code gets to production, environments, rollback procedure]

## Domain glossary
[Project-specific terms and their definitions]

## Common tasks
[How to add a feature, fix a bug, update dependencies, run migrations]

## Where to get help
[Contacts, channels, documentation links]
```

## Rules

1. Derive everything from the actual codebase -- do not fabricate
2. Flag gaps explicitly ("No CI/CD configuration found")
3. Keep the glossary to terms a newcomer would not know
4. Link to actual files using relative paths
5. If the audience is not specified, ask before generating
