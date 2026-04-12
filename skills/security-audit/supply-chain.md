---
title: Supply Chain Security
impact: HIGH
impactDescription: A compromised dependency executes with full application privileges
tags: supply-chain,dependencies,lockfile,typosquatting,sbom,npm-audit,cargo-audit,pip-audit
---

# Supply Chain Security

Dependency auditing, lockfile verification, typosquatting detection, and SBOM
generation. Complements the `dependency-auditor` skill with a security-first lens.

## Threat Model

Supply chain attacks target the weakest link between you and your dependencies:

| Attack vector | Example | Detection |
|---------------|---------|-----------|
| Typosquatting | `reqeusts` instead of `requests` | Name similarity check |
| Dependency confusion | Private package name claimed on public registry | Registry priority audit |
| Compromised maintainer | Legitimate package gets malicious update | Lockfile hash verification |
| Install scripts | `postinstall` runs `curl | sh` | Script audit, `--ignore-scripts` |
| Yanked/deleted package | Package removed after you depend on it | Lockfile pinning |
| Protestware | Maintainer adds destructive code intentionally | Version pinning, review diffs |

## Audit Commands by Ecosystem

### Python

```bash
# pip-audit: checks PyPI advisory database
pip-audit --require-hashes -r requirements.txt
pip-audit --fix  # auto-upgrade to patched versions

# safety: alternative scanner
safety check --full-report

# Check for typosquatting
pip install pip-safe
pip-safe check requirements.txt
```

### TypeScript / JavaScript

```bash
# npm audit: built-in advisory check
npm audit --audit-level=moderate
npm audit fix  # auto-upgrade compatible versions

# For yarn
yarn audit --level moderate

# For pnpm
pnpm audit --audit-level moderate

# Socket.dev: deeper analysis (install scripts, network access)
npx socket scan
```

Disable install scripts for untrusted packages:
```bash
npm install --ignore-scripts <package>
# Then manually review and run scripts if needed
```

### Go

```bash
# govulncheck: official Go vulnerability checker
govulncheck ./...

# Check if vulnerable code is actually called (reachability analysis)
govulncheck -show=traces ./...
```

### Rust

```bash
# cargo-audit: checks RustSec advisory database
cargo audit
cargo audit fix  # auto-upgrade to patched versions

# cargo-deny: comprehensive policy enforcement
cargo deny check advisories
cargo deny check licenses
cargo deny check bans
cargo deny check sources
```

### Elixir

```bash
# mix_audit: checks Elixir advisory database
mix deps.audit

# sobelow: Phoenix-specific security scanner
mix sobelow --config
```

## Lockfile Verification

Lockfiles are the last line of defense against supply chain attacks. They pin
exact versions and content hashes.

### What to check

1. **Lockfile exists and is committed** -- never .gitignore a lockfile
2. **Lockfile matches manifest** -- `npm ci` (not `npm install`) in CI
3. **No unexpected changes** -- review lockfile diffs in PRs
4. **Hashes are present** -- npm integrity hashes, pip `--require-hashes`

### CI enforcement

```yaml
# GitHub Actions: fail if lockfile is out of sync
- name: Verify lockfile
  run: |
    npm ci  # Fails if package-lock.json doesn't match package.json

# Python: require hashes
- name: Install with hash verification
  run: pip install --require-hashes -r requirements.txt
```

### Lockfile diff review

When reviewing PRs that modify lockfiles, check for:
- New dependencies you did not explicitly add (transitive additions)
- Version downgrades (potential rollback attack)
- Registry URL changes (dependency confusion)
- Removed integrity hashes

## Typosquatting Detection

Common patterns attackers use:
- Transposed characters: `reqeusts`, `djnago`
- Missing/extra characters: `request`, `requestss`
- Hyphen/underscore confusion: `python-dotenv` vs `python_dotenv`
- Scope squatting: `@company/utils` vs `company-utils`

### Manual checks

```bash
# Compare package names against known-good list
# Check download counts (typosquats have low downloads)
# Check publish date (recent publish of old-sounding name is suspicious)
# Check maintainer (single maintainer, no other packages)

# npm: check package info
npm info <package> --json | jq '{name, version, author, maintainers, time}'

# PyPI: check package info
pip show <package>
curl -s "https://pypi.org/pypi/<package>/json" | jq '{name: .info.name, author: .info.author, version: .info.version}'
```

## Dependency Confusion

When a project uses private packages, an attacker can register the same name on
the public registry with a higher version number. Package managers may prefer the
public version.

### Prevention

**npm**: Use scoped packages (`@company/package`) and configure registry:
```ini
# .npmrc
@company:registry=https://npm.company.com/
```

**Python**: Pin index URL and use `--extra-index-url` carefully:
```ini
# pip.conf
[global]
index-url = https://pypi.company.com/simple/
# Do NOT use --extra-index-url with private package names on public PyPI
```

**Go**: Use `GONOSUMCHECK` and `GOPRIVATE` for internal modules:
```bash
export GOPRIVATE=github.com/company/*
```

## SBOM Generation

Software Bill of Materials -- know exactly what ships in your artifact.

```bash
# Syft: generates SBOM from source or container
syft dir:. -o spdx-json > sbom.json
syft <image> -o cyclonedx-json > sbom.json

# Trivy: SBOM with vulnerability correlation
trivy fs --format spdx-json -o sbom.json .

# npm: built-in SBOM
npm sbom --sbom-format cyclonedx
```

## Supply Chain Audit Checklist

- [ ] All lockfiles committed and up to date
- [ ] CI uses `npm ci` / `pip install --require-hashes` (not `install`)
- [ ] No `postinstall` scripts from untrusted packages
- [ ] Private packages use scoped names or pinned registries
- [ ] `cargo-deny` / `pip-audit` / `npm audit` runs in CI
- [ ] Lockfile diffs are reviewed in PRs
- [ ] No packages with zero downloads or single anonymous maintainer
- [ ] SBOM generated for production artifacts
- [ ] Dependabot / Renovate configured for automated updates
- [ ] Known vulnerability scan runs on every PR
