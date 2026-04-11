---
title: Changelog Template
impact: MEDIUM
impactDescription: Poor changelogs erode user trust and cause missed breaking changes during upgrades
tags: changelog,keep-a-changelog,release-notes,documentation
---

# Changelog Template

Format and quality standards for generated changelogs following Keep a Changelog conventions.

## Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [3.0.0] - 2025-01-15

### Breaking Changes
- Remove v1 authentication endpoints; migrate to v2 OAuth2 PKCE
  ([migration guide](docs/v2-auth-migration.md))

### Added
- Fuzzy search matching with configurable Levenshtein threshold (#234)
- Bulk export endpoint for user data (#256)

### Changed
- Rate limiting now uses sliding window instead of fixed window

### Deprecated
- `GET /api/v2/users/search` query param `q` renamed to `query`
  (old param works until v4)

### Removed
- Legacy XML response format (use JSON)

### Fixed
- Pagination offset calculation returns duplicate results (#301)
- Memory leak in WebSocket connection pool (#298)

### Security
- Upgrade lodash to 4.17.21 (CVE-2021-23337)
```

## Grouping Rules

Map commit types to changelog sections:

| Commit Type | Changelog Section | Include? |
|-------------|-------------------|----------|
| feat        | Added             | Always   |
| fix         | Fixed             | Always   |
| perf        | Changed           | Always   |
| refactor    | Changed           | If user-visible |
| docs        | --                | Only if user-facing docs |
| style       | --                | Never    |
| test        | --                | Never    |
| chore       | --                | Only dep updates with CVEs |
| ci          | --                | Never    |
| build       | --                | Only if affects consumers |
| BREAKING    | Breaking Changes  | Always (top of changelog) |
| deprecation | Deprecated        | Always   |
| security    | Security          | Always   |

Sections with no entries are omitted entirely.

## Metadata Extraction

For each entry, extract and include:

- **Issue/PR reference** -- Link to the issue or PR (`#234`, `GH-234`)
- **Author** -- For multi-contributor projects, credit the author
- **Scope** -- If scoped commit, prefix the entry: `**auth:** add MFA support`
- **Migration action** -- For breaking changes, always include what the user must do

## Quality Checks

Before finalizing the changelog:

1. **User-meaningful language** -- Write for users, not developers. "Add search" not "Implement SearchService class". Avoid internal jargon.
2. **Breaking changes have migration steps** -- Every breaking change entry must include a concrete action: what to change in their code, config, or API calls.
3. **No duplicate entries** -- Merge commits that are part of the same logical change.
4. **Chronological within sections** -- Most impactful changes first within each group.
5. **Links work** -- Verify issue/PR links, migration guide links, and comparison URLs.
6. **Version comparison URLs** -- Add footer links for diff comparison:

```markdown
[3.0.0]: https://github.com/org/repo/compare/v2.3.1...v3.0.0
[2.3.1]: https://github.com/org/repo/compare/v2.3.0...v2.3.1
```
