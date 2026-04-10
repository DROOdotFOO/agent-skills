---
title: Secret Detection Patterns and Response Playbook
impact: CRITICAL
impactDescription: Missing a leaked credential in code leads to unauthorized access within minutes of public exposure.
tags: secrets, detection, regex, patterns, incident-response, playbook
---

# Secret Detection Patterns

## Detection Categories by Severity

### Critical -- Immediate rotation required

| Pattern | Regex | Service |
| ------- | ----- | ------- |
| AWS Access Key ID | `AKIA[0-9A-Z]{16}` | AWS IAM |
| AWS Secret Key | `aws_secret_access_key\s*=\s*['"]?[A-Za-z0-9/+]{40}` | AWS IAM |
| Stripe Live Key | `sk_live_[0-9a-zA-Z]{24,}` | Stripe |
| GitHub PAT | `ghp_[A-Za-z0-9]{36,}` | GitHub |
| GitHub Fine-grained | `github_pat_[A-Za-z0-9_]{82}` | GitHub |
| Private Key Block | `-----BEGIN (RSA\|EC\|DSA\|OPENSSH )?PRIVATE KEY-----` | Any |
| Google API Key | `AIza[0-9A-Za-z_-]{35}` | Google Cloud |

### High -- Likely sensitive, investigate and rotate

| Pattern | Regex | Service |
| ------- | ----- | ------- |
| Stripe Test Key | `sk_test_[0-9a-zA-Z]{24,}` | Stripe |
| Stripe Webhook Secret | `whsec_[0-9a-zA-Z]{32,}` | Stripe |
| Slack Token | `xox[baprs]-[0-9A-Za-z]{10,}` | Slack |
| Slack Webhook | `https://hooks\.slack\.com/services/[A-Z0-9]{9,}/[A-Z0-9]{9,}/[A-Za-z0-9]{24,}` | Slack |
| Twilio SID | `AC[a-z0-9]{32}` | Twilio |
| Twilio Auth Token | `SK[a-z0-9]{32}` | Twilio |
| Google OAuth Client | `[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com` | Google |
| DB Connection with creds | `(postgres\|mysql\|mongodb)://[^:]+:[^@]+@` | Database |
| Redis with auth | `redis://:[^@]+@` | Redis |
| PEM Certificate | `-----BEGIN CERTIFICATE-----` | TLS/SSL |

### Medium -- Possible exposure, verify context

| Pattern | Regex | Notes |
| ------- | ----- | ----- |
| Hardcoded JWT | `eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}` | May be test tokens |
| Generic secret assignment | `(secret\|password\|passwd\|api_key\|apikey\|token)\s*[:=]\s*['"][^'"]{12,}['"]` | High false positive rate |

## Severity Guidance

- **Critical**: treat as active incident. Revoke immediately, then investigate.
- **High**: likely a real credential. Investigate within hours, rotate if confirmed.
- **Medium**: possible exposure. Verify context (test fixture? documentation?). Sanitize where needed.

## Response Playbook

When a secret is detected:

1. **Revoke or rotate** the exposed credential at the provider level immediately
2. **Identify blast radius** -- which services, environments, and users are affected?
3. **Remove from code/history** -- `git filter-repo` or BFG Repo-Cleaner if in git history
4. **Add preventive controls** -- pre-commit hooks, CI secret scanning gates
5. **Verify monitoring** -- check access logs for unauthorized usage during exposure window
6. **Document** -- file incident report with scope, timeline, and remediation steps

## False Positive Management

- Maintain `.gitleaksignore` or `.secrets.baseline` in version control so the whole team shares exclusions
- Review false positive lists during security audits -- patterns may mask real leaks over time
- Prefer tightening regex patterns over broadly ignoring files
- Test/mock/fixture files should use obviously fake values (`sk_test_FAKE`, `AKIAIOSFODNN7EXAMPLE`)
