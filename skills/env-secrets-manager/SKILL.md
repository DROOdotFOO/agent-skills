---
name: env-secrets-manager
description: >
  Environment variable hygiene, secret leak detection, and credential rotation workflows.
  TRIGGER when: working with .env files, secret management, credential rotation,
  pre-commit secret scanning, or investigating leaked credentials.
  DO NOT TRIGGER when: general config file editing, non-secret environment setup,
  or infrastructure provisioning (use relevant infra skill).
metadata:
  author: alirezarezvani
  version: "1.0.0"
  tags: secrets, env, security, leak-detection, rotation, pre-commit, gitignore
  license: MIT
---

# Env & Secrets Manager

Manage environment-variable hygiene and secrets safety across local development and production workflows. Covers auditing, leak detection, rotation, and preventive controls.

## What You Get

- Secret leak detection with regex-based scanning (staged files and git history)
- Severity-based findings (critical/high/medium) with response playbook
- Credential rotation workflows (AWS, Stripe, GitHub PAT, DB, JWT)
- Cloud secret store integration guidance (Vault, AWS SM, Azure KV, GCP SM)
- CI/CD secret injection patterns (GitHub Actions, GitLab CI)
- Pre-commit detection setup (gitleaks, detect-secrets)

## When to Use

- Before pushing commits that touched env/config files
- During security audits and incident triage
- When onboarding contributors who need safe env conventions
- When validating that no obvious secrets are hardcoded

## Recommended Workflow

1. Scan the repository for likely secret leaks (see `references/secret-patterns.md`)
2. Prioritize `critical` and `high` findings first
3. Rotate real credentials and remove exposed values
4. Update `.env.example` and `.gitignore` as needed
5. Add or tighten pre-commit/CI secret scanning gates

## WRONG: secrets in code and examples

```bash
# WRONG: real credentials in .env.example
DATABASE_URL=postgres://admin:s3cret@prod.db.internal/myapp
STRIPE_SECRET_KEY=sk_live_abc123xyz
```

## CORRECT: placeholders only

```bash
# CORRECT: .env.example with safe placeholders
DATABASE_URL=postgres://user:password@localhost/myapp_dev
STRIPE_SECRET_KEY=sk_test_REPLACE_ME
```

## Common Pitfalls

| Mistake | Why it's bad |
| ------- | ------------ |
| Committing real values in `.env.example` | Example files get pushed; real secrets in git history |
| Rotating one system but missing downstream consumers | Partial rotation causes outages |
| Logging secrets during debugging | Logs persist in CI artifacts, observability platforms |
| Treating suspected leaks as low urgency | Automated scrapers act within minutes of public exposure |
| Using `echo` on secrets in CI pipelines | Even with masking, secrets can leak via `toJSON()` or redirects |

## Best Practices

1. Use a secret manager as the production source of truth (never `.env` in prod)
2. Keep dev env files local and gitignored
3. Enforce detection in CI before merge
4. Re-test application paths immediately after credential rotation
5. Commit only `.env.example`, never `.env`

## Reference Docs

| File | Contents |
| ---- | -------- |
| `references/secret-patterns.md` | Detection regex by severity, response playbook |
| `references/rotation-and-detection.md` | Validation scripts, scanning tools, rotation workflow, pre-commit setup, cloud stores, CI/CD patterns |

## Cloud Secret Store Quick Reference

| Provider | Best For | Key Feature |
| -------- | -------- | ----------- |
| HashiCorp Vault | Multi-cloud / hybrid | Dynamic secrets, policy engine |
| AWS Secrets Manager | AWS-native | Lambda/ECS/EKS integration, auto RDS rotation |
| Azure Key Vault | Azure-native | Managed HSM, Azure AD RBAC |
| GCP Secret Manager | GCP-native | IAM-based access, versioning |
| 1Password | Developer workflows | CLI (`op`), Connect server, SSH agent |

**Selection:** Single cloud -> cloud-native store. Multi-cloud -> Vault. Developer/team -> 1Password or Doppler.
