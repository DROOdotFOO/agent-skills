---
name: release
description: |
  Release management with changelog generation, semantic versioning, and readiness checks.
  TRIGGER when: user asks to prepare a release, generate a changelog, bump version, check release readiness, or create a release tag; user runs /release or /changelog.
  DO NOT TRIGGER when: writing commit messages (use conventional commits directly), deploying to infrastructure, debugging production issues.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: release,changelog,semver,versioning,conventional-commits,ci-cd
---

# Release Skill

End-to-end release management: parse conventional commits, determine the version bump, generate a changelog, run readiness checks, and create the release.

## Workflow

1. **Parse commits** -- Collect commits since last release tag. Classify by type. See [conventional-commits.md](conventional-commits.md).
2. **Determine version bump** -- Apply SemVer rules: BREAKING CHANGE -> major, feat -> minor, everything else -> patch.
3. **Generate changelog** -- Group changes by category, write user-meaningful descriptions. See [changelog-template.md](changelog-template.md).
4. **Readiness checks** -- Validate pre-release conditions. See [readiness-checklist.md](readiness-checklist.md).
5. **Verify** -- Run the full test suite on the exact commit being tagged. Show the output. Do not tag a commit you have not tested in this session.
6. **Create release** -- Tag the commit, push tag, create GitHub release with changelog body.

## Version Bump Logic

```
Current: 2.3.1
Commits since v2.3.1:
  feat: add search API         -> minor
  fix: correct pagination      -> patch
  feat!: redesign auth flow    -> major (BREAKING)

Result: BREAKING wins -> v3.0.0
```

When multiple bump types conflict, the highest wins: major > minor > patch.

## Output Format

```
Release: v3.0.0 (from v2.3.1)
Bump reason: BREAKING CHANGE in auth flow redesign
Changelog: 2 features, 1 fix, 0 breaking migration notes
Readiness: 8/9 checks passed (WARN: no stakeholder sign-off)
Action: Tag and push? [y/n]
```

## What You Get

- A semantically versioned release tag with the correct bump (major/minor/patch) derived from conventional commits
- A generated changelog grouped by category (features, fixes, breaking changes) with user-meaningful descriptions
- A readiness report showing which pre-release checks passed or failed, with warnings for anything unresolved

## Sub-files

| File                                               | Content                                    |
|----------------------------------------------------|--------------------------------------------|
| [conventional-commits.md](conventional-commits.md) | Commit types, SemVer mapping, linting      |
| [changelog-template.md](changelog-template.md)     | Changelog format, grouping, quality checks |
| [readiness-checklist.md](readiness-checklist.md)    | Pre-release validation, DORA, rollback     |
