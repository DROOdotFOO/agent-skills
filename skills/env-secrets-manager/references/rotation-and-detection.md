---
title: Secret Validation, Detection Scripts, and Rotation Workflows
impact: CRITICAL
impactDescription: Incomplete rotation or missed detection leaves credentials exposed to automated scraping within minutes.
tags: secrets, rotation, detection, scanning, pre-commit, gitleaks, ci-cd, validation
---

# Validation, Detection & Rotation

## Env Validation Script

Validate required environment variables at app startup or in CI:

```bash
#!/bin/bash
set -euo pipefail

MISSING=()

ALWAYS_REQUIRED=(
  APP_SECRET
  DATABASE_URL
  AUTH_JWT_SECRET
)

for var in "${ALWAYS_REQUIRED[@]}"; do
  if [ -z "${!var:-}" ]; then
    MISSING+=("$var")
  fi
done

if [ "${APP_ENV:-}" = "production" ] || [ "${NODE_ENV:-}" = "production" ]; then
  PROD_REQUIRED=(STRIPE_SECRET_KEY SENTRY_DSN)
  for var in "${PROD_REQUIRED[@]}"; do
    if [ -z "${!var:-}" ]; then
      MISSING+=("$var (required in production)")
    fi
  done
fi

if [ ${#MISSING[@]} -gt 0 ]; then
  printf "FATAL: Missing required environment variables:\n"
  for var in "${MISSING[@]}"; do
    printf "  - %s\n" "$var"
  done
  printf "\nCopy .env.example to .env and fill in missing values.\n"
  exit 1
fi

printf "All required environment variables are set\n"
```

---

## Secret Scanning

### Scan staged files (pre-commit)

```bash
#!/bin/bash
set -euo pipefail

FAIL=0

check() {
  local label="$1"
  local pattern="$2"
  local matches

  matches=$(git diff --cached -U0 2>/dev/null | grep "^+" | grep -vE "^(\+\+\+|#|//)" | \
    grep -E "$pattern" | grep -v ".env.example" | grep -v "test\|mock\|fixture\|fake" || true)

  if [ -n "$matches" ]; then
    printf "SECRET DETECTED [%s]:\n%s\n" "$label" "$(echo "$matches" | head -5)"
    FAIL=1
  fi
}

check "AWS Access Key"    "AKIA[0-9A-Z]{16}"
check "Stripe Live Key"   "sk_live_[0-9a-zA-Z]{24,}"
check "GitHub Token"      "gh[ps]_[A-Za-z0-9]{36,}"
check "Private Key Block" "-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
check "Generic Secret"    "(secret|password|api_key|token)\s*[:=]\s*['\"][^'\"]{12,}['\"]"
check "DB Connection"     "(postgres|mysql|mongodb)://[^:]+:[^@]+@"

if [ "$FAIL" -eq 1 ]; then
  printf "\nBLOCKED: Secrets detected in staged changes.\n"
  exit 1
fi

printf "No secrets detected in staged changes.\n"
```

### Scan git history (post-incident)

```bash
#!/bin/bash
set -euo pipefail

PATTERNS=(
  "AKIA[0-9A-Z]{16}"
  "sk_live_[0-9a-zA-Z]{24}"
  "-----BEGIN.*PRIVATE KEY-----"
  "ghp_[A-Za-z0-9]{36}"
)

for pattern in "${PATTERNS[@]}"; do
  printf "Scanning for: %s\n" "$pattern"
  git log --all -p --no-color 2>/dev/null | \
    grep -n "$pattern" | grep "^+" | grep -v "^+++" | head -10 || true
done
```

---

## Pre-Commit Setup

### gitleaks

```toml
# .gitleaks.toml
[extend]
useDefault = true

[[rules]]
id = "custom-internal-token"
description = "Internal service token pattern"
regex = '''INTERNAL_TOKEN_[A-Za-z0-9]{32}'''
secretGroup = 0
```

Install: `brew install gitleaks`
Hook: `gitleaks git --pre-commit --staged`
Baseline: `gitleaks detect --source . --report-path gitleaks-report.json`

### detect-secrets

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

Generate baseline: `detect-secrets scan --all-files > .secrets.baseline`
Audit: `detect-secrets audit .secrets.baseline`

---

## Credential Rotation Workflow

### Step 1 -- Detect & confirm

```bash
# Find first commit that introduced the secret
git log --all -p --no-color -- "*.env" "*.json" "*.yaml" | \
  grep -B 10 "THE_LEAKED_VALUE" | grep "^commit" | tail -1
```

### Step 2 -- Rotate per service

| Service | Action |
| ------- | ------ |
| AWS | IAM console -> delete access key -> create new -> update all consumers |
| Stripe | Dashboard -> Developers -> API keys -> Roll key |
| GitHub PAT | Settings -> Developer Settings -> Tokens -> Revoke -> Create new |
| Database | `ALTER USER app_user PASSWORD 'new-password';` |
| JWT secret | Rotate key (all existing sessions invalidated) |

### Step 3 -- Update all environments

```bash
# Vault KV v2
vault kv put secret/myapp/prod \
  STRIPE_SECRET_KEY="sk_live_NEW..."

# AWS SSM
aws ssm put-parameter \
  --name "/myapp/prod/STRIPE_SECRET_KEY" \
  --value "sk_live_NEW..." \
  --type "SecureString" --overwrite

# 1Password
op item edit "MyApp Prod" \
  --field "STRIPE_SECRET_KEY[password]=sk_live_NEW..."
```

### Step 4 -- Remove from git history

```bash
# WARNING: rewrites history -- coordinate with team
git filter-repo --replace-text <(echo "LEAKED_VALUE==>REDACTED")
git push origin --force --all
```

### Step 5 -- Verify

```bash
# Confirm removed from history
git log --all -p | grep "LEAKED_VALUE" | wc -l  # should be 0

# Test new credentials work
curl -H "Authorization: Bearer $NEW_TOKEN" https://api.service.com/test
```

---

## CI/CD Secret Injection

### GitHub Actions

- Use **repository/environment secrets** via `${{ secrets.SECRET_NAME }}`
- Prefer **OIDC federation** over long-lived access keys
- Environment secrets with required reviewers add approval gates
- Never `echo` or `toJSON()` on secret values

### GitLab CI

- Store as **CI/CD variables** with `masked` and `protected` flags
- Use **Vault integration** (`secrets:vault`) for dynamic injection
- Scope variables to specific environments

### Universal rules

- Never echo/print secret values in pipeline output
- Use short-lived tokens (OIDC, STS AssumeRole) over static credentials
- Restrict PR access -- don't expose secrets to fork-triggered pipelines
- Rotate CI secrets on the same schedule as application secrets
