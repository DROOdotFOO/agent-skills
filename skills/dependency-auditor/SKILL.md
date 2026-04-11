---
name: dependency-auditor
description: |
  Multi-language dependency vulnerability scanning and license compliance auditing.
  TRIGGER when: user asks to audit dependencies, check for vulnerabilities, review licenses, detect outdated or bloated packages, or assess supply chain risk.
  DO NOT TRIGGER when: user is adding a specific dependency they have already chosen, or debugging a build failure unrelated to dependency versions.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: security, dependencies, vulnerabilities, licenses, audit, supply-chain
---

# Dependency Auditor

## Philosophy

Dependencies are attack surface. Every transitive dependency is code you did not write, did not review, and may not maintain. Audit proactively, not after an incident.

## Workflow: 5 Phases

### Phase 1: Scan Dependencies

Detect the project's ecosystem(s) from lockfiles and manifests. A single project may use multiple ecosystems (e.g., Node frontend + Python backend). Identify:
- Direct dependencies and their versions
- Transitive dependency tree depth
- Pinned vs floating version specifiers

### Phase 2: Vulnerability Check

Run ecosystem-specific audit commands. See [vulnerability-scanning.md](vulnerability-scanning.md) for per-language tools. For each vulnerability:
- CVE identifier and CVSS score
- Affected version range
- Whether a patched version exists
- Whether the vulnerable code path is reachable in this project

### Phase 3: License Audit

Classify every dependency's license. See [license-compliance.md](license-compliance.md) for the taxonomy. Flag:
- Copyleft licenses in proprietary projects
- License conflicts between dependencies
- Dependencies with no declared license
- Dual-licensed packages where the commercial license applies

### Phase 4: Detect Bloat

Identify dependencies that are:
- Unused (imported but never called)
- Duplicated (multiple versions of the same package)
- Oversized relative to their function (pulling in a framework for one utility)
- Replaceable with standard library equivalents

### Phase 5: Upgrade Plan

For each actionable finding, produce:
- Priority (critical vuln > license issue > bloat)
- Recommended action (upgrade, replace, remove, pin)
- Breaking change risk for each upgrade
- Test commands to verify the upgrade

## Polyglot Coverage

| Ecosystem | Manifest | Lockfile | Audit Tool |
|-----------|----------|----------|------------|
| JavaScript/TypeScript | package.json | package-lock.json, yarn.lock, pnpm-lock.yaml | npm audit, yarn audit |
| Python | pyproject.toml, requirements.txt | poetry.lock, uv.lock | pip-audit, safety |
| Go | go.mod | go.sum | govulncheck |
| Rust | Cargo.toml | Cargo.lock | cargo-audit |
| Ruby | Gemfile | Gemfile.lock | bundler-audit |
| Elixir | mix.exs | mix.lock | mix_audit, sobelow |
| Java/Kotlin | pom.xml, build.gradle | | dependency-check |

## Sub-files

| File | Topic |
|------|-------|
| [vulnerability-scanning.md](vulnerability-scanning.md) | Per-language audit commands, CVSS, supply chain |
| [license-compliance.md](license-compliance.md) | License classification, GPL contamination, SPDX |
