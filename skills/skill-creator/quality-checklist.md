---
title: Quality Checklist and Anti-patterns
impact: HIGH
impactDescription: Poor skill design leads to false triggers, missed activations, and unhelpful context injection
tags: quality, review, anti-patterns, checklist
---

# Quality Checklist

Use this to review a skill before committing.

## Must-have checklist

- [ ] `name` field matches directory name
- [ ] Description has `TRIGGER when:` with concrete signals (file types, imports, phrases)
- [ ] Description has `DO NOT TRIGGER when:` excluding adjacent domains
- [ ] `metadata.version` is a quoted string (`"1.0.0"` not `1.0`)
- [ ] Tags are comma-separated strings, not YAML arrays
- [ ] Sub-files have `impact`, `impactDescription`, and `tags` frontmatter
- [ ] Reading guide file references point to real files
- [ ] See-also references point to real skill directories
- [ ] `./scripts/skills-lint.sh` passes with zero errors

## Should-have checklist

- [ ] Sub-files contain incorrect/correct example pairs with explanations
- [ ] Trigger clauses mention at least two distinct signal types (file, import, phrase)
- [ ] At least one sub-file is `CRITICAL` or `HIGH` impact
- [ ] Skill covers one coherent domain, not a grab-bag of topics
- [ ] Pitfalls table identifies at least three common mistakes

## Anti-patterns

### Too broad

```yaml
# BAD: triggers on everything remotely related to APIs
description: >
  API skill. TRIGGER when: user works with APIs.
  DO NOT TRIGGER when: not working with APIs.
```

**Problem:** Activates constantly, drowning out other skills. The DO NOT
TRIGGER is just the negation of the trigger, which adds no information.

**Fix:** Narrow to a specific API concern (design, security, testing) and
name concrete file types or tools.

### Too narrow

```yaml
# BAD: only triggers on one exact phrase
description: >
  Help with Express.js middleware error handling.
  TRIGGER when: user says "express middleware error".
  DO NOT TRIGGER when: anything else.
```

**Problem:** Almost never activates. Too specific to justify a standalone
skill -- this should be a section in a broader Node.js or error-handling
skill.

**Fix:** Broaden to cover the parent domain (Express patterns, or Node.js
error handling) while keeping triggers precise.

### Missing examples

A skill with only rules and no incorrect/correct pairs forces Claude to
guess what compliance looks like. Every non-trivial claim should have a
concrete code or config example showing the right and wrong way.

### Trigger/content mismatch

```yaml
description: >
  React component patterns. TRIGGER when: working with .tsx files.
  DO NOT TRIGGER when: working with Vue or Angular.
```

But the skill body only covers state management. If the trigger fires on
any `.tsx` file but the content only helps with state, the skill wastes
context window on irrelevant activations.

**Fix:** Either narrow the trigger to state-management signals or broaden
the content to cover React component patterns generally.

### Giant monolith skill

A single SKILL.md with 2000+ lines covering everything about a domain.
This loads the entire context even when only a small part is relevant.

**Fix:** Split into focused sub-files. SKILL.md should be an overview with
a reading guide. Let Claude load sub-files on demand based on the specific
task.

### Duplicate coverage

Two skills that trigger on the same signals and cover the same content.
This wastes context and can produce conflicting advice.

**Fix:** Before creating a new skill, search existing skills for overlap.
Either extend the existing skill or clearly delineate boundaries with
distinct triggers.

## Review questions

When reviewing a skill (your own or someone else's), ask:

1. **Would I know when this skill activates?** Read the trigger clause --
   can you enumerate the exact conditions without guessing?
2. **Does the DO NOT TRIGGER exclude real confusion cases?** Think of the
   two or three most likely false-positive scenarios.
3. **Could a junior developer follow the examples?** The incorrect/correct
   pairs should be self-explanatory without reading prose.
4. **Is the scope right?** Too broad = noisy activation. Too narrow =
   never activates. A good skill covers one coherent domain with 2-6
   sub-files.
5. **Does it pass the linter?** Run `./scripts/skills-lint.sh` -- zero
   errors, zero warnings is the target.
