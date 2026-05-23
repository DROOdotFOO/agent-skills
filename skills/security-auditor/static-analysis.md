---
title: Static Analysis
impact: HIGH
impactDescription: Automated static analysis catches vulnerability classes that manual review misses
tags: semgrep,bandit,gosec,cargo-audit,eslint,trivy,sast,ci
---

# Static Analysis

Language-specific security linters, semgrep rules, and CI integration patterns.

## Tool Matrix

| Language   | Tool                | Install                        | Run                                      |
|------------|---------------------|--------------------------------|------------------------------------------|
| Python     | bandit              | `pip install bandit`           | `bandit -r src/ -f json`                 |
| Python     | semgrep             | `pip install semgrep`          | `semgrep --config=p/python`              |
| TypeScript | eslint-plugin-security | `npm i -D eslint-plugin-security` | Configure in eslint config           |
| TypeScript | semgrep             | `npm i -g semgrep`             | `semgrep --config=p/typescript`          |
| Go         | gosec               | `go install github.com/securego/gosec/v2/cmd/gosec@latest` | `gosec ./...`  |
| Go         | govulncheck         | `go install golang.org/x/vuln/cmd/govulncheck@latest` | `govulncheck ./...`    |
| Rust       | cargo-audit         | `cargo install cargo-audit`    | `cargo audit`                            |
| Rust       | cargo-deny          | `cargo install cargo-deny`     | `cargo deny check`                       |
| Multi      | trivy               | `brew install trivy`           | `trivy fs --scanners vuln,secret .`      |
| Multi      | gitleaks            | `brew install gitleaks`        | `gitleaks detect --source .`             |
| Multi      | trufflehog          | `brew install trufflehog`      | `trufflehog filesystem --directory .`    |

## Semgrep: Custom Rules

Semgrep is the highest-leverage tool. It supports custom rules in YAML that match
AST patterns across languages.

### SQL injection detection (Python)

```yaml
rules:
  - id: sql-injection-format-string
    patterns:
      - pattern: |
          $DB.execute(f"...{$VAR}...")
      - pattern-not: |
          $DB.execute(f"...{$CONST}...", ...)
    message: "SQL injection via f-string interpolation"
    languages: [python]
    severity: ERROR
    metadata:
      cwe: "CWE-89"
      owasp: "A03:2021"
```

### Command injection detection (Python)

```yaml
rules:
  - id: command-injection-os-system
    pattern: os.system($CMD)
    message: "Use subprocess.run() with a list instead of os.system()"
    languages: [python]
    severity: ERROR
    metadata:
      cwe: "CWE-78"

  - id: command-injection-shell-true
    pattern: subprocess.run($CMD, ..., shell=True, ...)
    message: "shell=True enables shell injection -- use a list of args"
    languages: [python]
    severity: WARNING
    metadata:
      cwe: "CWE-78"
```

### Unsafe deserialization (Python)

```yaml
rules:
  - id: pickle-loads
    pattern: pickle.loads(...)
    message: "pickle.loads() on untrusted data is RCE"
    languages: [python]
    severity: ERROR
    metadata:
      cwe: "CWE-502"

  - id: yaml-unsafe-load
    pattern: yaml.load($DATA)
    fix: yaml.safe_load($DATA)
    message: "yaml.load() without Loader allows arbitrary code execution"
    languages: [python]
    severity: ERROR
    metadata:
      cwe: "CWE-502"
```

### SSRF detection (TypeScript)

```yaml
rules:
  - id: ssrf-fetch-user-input
    patterns:
      - pattern: fetch($URL, ...)
      - pattern-where-python: |
          # Flag when URL comes from request params
          "req." in str(vars.get("$URL", ""))
    message: "Potential SSRF -- validate URL before fetching"
    languages: [typescript, javascript]
    severity: WARNING
    metadata:
      cwe: "CWE-918"
```

### Path traversal detection (Go)

```yaml
rules:
  - id: path-traversal-join
    patterns:
      - pattern: filepath.Join($BASE, $INPUT)
      - pattern-not-inside: |
          if !strings.HasPrefix(...) { ... }
    message: "Path traversal -- validate joined path stays within base directory"
    languages: [go]
    severity: ERROR
    metadata:
      cwe: "CWE-22"
```

## Language-Specific Linter Configuration

### Python: bandit

```ini
# .bandit (or pyproject.toml [tool.bandit])
[bandit]
skips = []
exclude_dirs = [tests, .venv]
```

Key bandit checks:
- B101: assert used (disabled in test dirs)
- B105-B107: hardcoded passwords
- B301-B303: pickle, marshal, shelve
- B311: random (not crypto-safe)
- B501-B502: no certificate verification
- B601-B602: shell injection via subprocess
- B608: SQL injection via string formatting

### TypeScript: eslint-plugin-security

```json
{
  "plugins": ["security"],
  "extends": ["plugin:security/recommended-legacy"],
  "rules": {
    "security/detect-object-injection": "warn",
    "security/detect-non-literal-regexp": "warn",
    "security/detect-unsafe-regex": "error",
    "security/detect-buffer-noassert": "error",
    "security/detect-eval-with-expression": "error",
    "security/detect-no-csrf-before-method-override": "error",
    "security/detect-possible-timing-attacks": "warn"
  }
}
```

### Go: gosec

```yaml
# .gosec.yaml
global:
  audit: enabled
rules:
  G101: true  # Hardcoded credentials
  G201: true  # SQL string formatting
  G202: true  # SQL string concatenation
  G301: true  # Mkdir with permissive perms
  G304: true  # File path from variable
  G401: true  # Weak crypto (MD5, SHA1)
  G501: true  # Blacklisted imports (crypto/md5)
```

### Rust: cargo-deny

```toml
# deny.toml
[advisories]
vulnerability = "deny"
unmaintained = "warn"
yanked = "deny"

[licenses]
unlicensed = "deny"
default = "deny"
allow = ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"]

[bans]
multiple-versions = "warn"
wildcards = "deny"

[sources]
unknown-registry = "deny"
unknown-git = "deny"
```

## CI Integration

### GitHub Actions

```yaml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Semgrep
        uses: semgrep/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/owasp-top-ten

      - name: Trivy (vulnerabilities + secrets)
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scanners: vuln,secret
          severity: CRITICAL,HIGH

      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2
```

### Pre-commit hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.8
    hooks:
      - id: bandit
        args: ["-r", "src/"]

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks

  - repo: https://github.com/semgrep/semgrep
    rev: v1.60.0
    hooks:
      - id: semgrep
        args: ["--config=p/python", "--error"]
```

## Triage Workflow

Not every finding is a real vulnerability. Triage by asking:

1. **Is the input attacker-controlled?** If the value comes from a config file only
   admins can edit, the risk is lower.
2. **Is the code reachable?** Dead code or test-only code has lower priority.
3. **Is there defense in depth?** A SQL injection behind a WAF and parameterized ORM
   is different from raw SQL in a public endpoint.
4. **What is the blast radius?** Read-only SQL injection is less severe than one that
   can modify or exfiltrate data.

Mark findings as: CONFIRMED, FALSE POSITIVE (with justification), or NEEDS INVESTIGATION.
