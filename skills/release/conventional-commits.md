---
title: Conventional Commits
impact: HIGH
impactDescription: Incorrect commit classification produces wrong version bumps and misleading changelogs
tags: conventional-commits,semver,commit-linting,monorepo
---

# Conventional Commits

Full taxonomy of commit types, their SemVer implications, and linting rules.

## Commit Format

```
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

The `!` after type/scope indicates a BREAKING CHANGE. The footer `BREAKING CHANGE: <description>` is equivalent.

## Type Taxonomy

| Type       | SemVer  | Description                                       |
|------------|---------|---------------------------------------------------|
| `feat`     | minor   | New feature visible to users                      |
| `fix`      | patch   | Bug fix for existing functionality                |
| `docs`     | patch   | Documentation only (README, API docs, comments)   |
| `style`    | patch   | Formatting, whitespace, semicolons (no logic)     |
| `refactor` | patch   | Code change that neither fixes a bug nor adds feature |
| `perf`     | patch   | Performance improvement with no API change        |
| `test`     | patch   | Adding or correcting tests                        |
| `chore`    | patch   | Build process, tooling, dependency updates        |
| `ci`       | patch   | CI/CD configuration changes                       |
| `build`    | patch   | Build system or external dependency changes       |

### SemVer Override Rules

- Any type with `!` or `BREAKING CHANGE` footer -> **major** (overrides type default)
- `feat` -> **minor** (unless breaking)
- All other types -> **patch**
- Pre-1.0.0: breaking changes bump minor instead of major (`0.x.y`)

## Scope Convention

Scopes identify the affected module or area:

```
feat(auth): add OAuth2 PKCE flow
fix(api/users): correct pagination offset
chore(deps): bump express to 4.19
```

### Monorepo Scope Filtering

In monorepos, scope maps to package names. When generating a changelog for a specific package, only include commits whose scope matches:

```
# Only affects @myorg/auth package
feat(auth): add MFA support        -> include in auth changelog
fix(api): correct rate limiting     -> exclude from auth changelog
feat: global logging overhaul       -> include in all changelogs (no scope)
```

Unscoped commits apply to all packages unless the body specifies otherwise.

## Commit Linting Rules

Enforce via commitlint, git hooks, or CI:

- **Type required** -- Reject commits without a valid type prefix
- **Subject max length** -- 50 characters for subject line (72 for body lines)
- **Subject lowercase** -- No capital first letter after the colon
- **No period** -- Subject line does not end with `.`
- **Body separation** -- Blank line between subject and body
- **Breaking change format** -- Footer must be `BREAKING CHANGE: <description>` (not `BREAKING-CHANGE` or lowercase)
- **Imperative mood** -- "add feature" not "added feature" or "adds feature"

## Examples

```
feat(search): add fuzzy matching to product search

Implements Levenshtein distance matching with configurable
threshold. Default threshold is 2 edits.

Closes #234

---

fix!: remove deprecated v1 authentication endpoints

BREAKING CHANGE: The /api/v1/auth/* endpoints have been removed.
Migrate to /api/v2/auth/* which uses OAuth2 PKCE.
See migration guide: docs/v2-auth-migration.md

---

chore(deps): bump lodash from 4.17.20 to 4.17.21

Addresses CVE-2021-23337 (command injection in template).
```
