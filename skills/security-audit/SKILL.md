---
name: security-audit
description: |
  General-purpose application security auditing across Python, TypeScript, Go, and Rust.
  TRIGGER when: user asks for a security audit, vulnerability assessment, threat modeling,
  code security review, OWASP analysis, variant analysis, or asks about injection, XSS,
  SSRF, path traversal, deserialization, or crypto misuse in application code.
  DO NOT TRIGGER when: working with .sol files, smart contracts, or Solidity audits
  (use solidity-audit); when reviewing code for general quality without security focus
  (use code-review); when auditing dependencies only (use dependency-auditor).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: security, audit, owasp, injection, xss, ssrf, variant-analysis, appsec
---

# security-audit

General-purpose application security auditing. Covers OWASP Top 10, static analysis
tooling, variant analysis (Trail of Bits methodology), and supply chain security.
Polyglot: Python, TypeScript, Go, Rust.

## Philosophy

Assume the attacker controls all user input, all HTTP headers, all query parameters,
all file uploads, and all environment variables that are not hardcoded. Every trust
boundary crossing is a potential exploit. Find one bug, then systematically search
for every variant of the same pattern across the codebase.

## Audit Workflow: 4 Phases

### Phase 1: Attack Surface Mapping

Identify all trust boundary crossings:
- HTTP endpoints (routes, controllers, handlers)
- CLI argument parsing
- File I/O (reads, writes, path construction)
- Database queries (raw SQL, ORM query builders)
- External service calls (APIs, DNS, SMTP)
- Deserialization points (JSON, YAML, pickle, protobuf)
- Template rendering (server-side, email templates)
- Subprocess/command execution
- Cryptographic operations

### Phase 2: Vulnerability Scan

Run static analysis tools and manual pattern matching against the attack surface.
See [vulnerability-patterns.md](vulnerability-patterns.md) for OWASP Top 10 with
incorrect/correct code examples per language. See [static-analysis.md](static-analysis.md)
for tool configuration and semgrep rules.

### Phase 3: Variant Analysis

When you find a vulnerability, systematically search for every instance of the same
pattern. See [variant-analysis.md](variant-analysis.md) for the Trail of Bits methodology:
find, characterize, search, verify.

### Phase 4: Supply Chain Review

Audit dependencies for known vulnerabilities, typosquatting, and malicious packages.
See [supply-chain.md](supply-chain.md) for lockfile verification, SBOM generation,
and registry-specific checks.

## Severity Classification

| Severity | Criteria |
|----------|----------|
| CRITICAL | RCE, auth bypass, SQL injection with data exfil, deserialization of untrusted data |
| HIGH     | Stored XSS, SSRF to internal services, path traversal with file read, privilege escalation |
| MEDIUM   | Reflected XSS, open redirect, verbose error messages leaking internals, weak crypto |
| LOW      | Missing security headers, cookie flags, CSRF on non-state-changing endpoints |
| INFO     | Hardening recommendations, defense-in-depth suggestions |

## When to use

This skill activates when auditing application code for security vulnerabilities
across any language except Solidity.

## When NOT to use

- For Solidity / smart contract audits -- use `solidity-audit`
- For general code review without security focus -- use `code-review`
- For dependency-only audits -- use `dependency-auditor`

## See also

- `solidity-audit` -- for smart contract security
- `code-review` -- for general code quality review
- `dependency-auditor` -- for dependency vulnerability scanning
- `env-secrets-manager` -- for secret leak detection and rotation

## Reading guide

| Working on | Read |
|------------|------|
| OWASP Top 10 patterns with code examples | [vulnerability-patterns.md](vulnerability-patterns.md) |
| Static analysis tools and semgrep rules | [static-analysis.md](static-analysis.md) |
| Trail of Bits variant analysis methodology | [variant-analysis.md](variant-analysis.md) |
| Dependency and supply chain auditing | [supply-chain.md](supply-chain.md) |
