---
name: ci-cd-pipeline-builder
description: |
  Detect project stack and generate CI/CD pipeline configuration for GitHub Actions or GitLab CI.
  TRIGGER when: user asks to set up CI/CD, create a pipeline, add GitHub Actions, configure GitLab CI, or automate testing and deployment.
  DO NOT TRIGGER when: user is debugging an existing pipeline failure, or asking about deployment infrastructure (servers, containers, cloud).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: ci-cd, github-actions, gitlab-ci, pipeline, automation, devops
---

# CI/CD Pipeline Builder

## Philosophy

Start with a minimal reliable pipeline that runs tests on every push. Add complexity only when justified. A pipeline that is fast and trustworthy is better than one that is comprehensive and flaky.

## Workflow: 5 Phases

### Phase 1: Detect Stack

Scan the repository for manifests, lockfiles, and configuration files. See [stack-detection.md](stack-detection.md) for the full signal table. Identify:
- Primary language(s) and runtime versions
- Package manager and lockfile
- Test framework and test command
- Linter and formatter
- Build tool and build command
- Monorepo structure (if applicable)

### Phase 2: Choose Platform

Default to GitHub Actions unless the project already uses GitLab CI or the user requests otherwise. Check for existing pipeline files:
- `.github/workflows/*.yml` -- GitHub Actions
- `.gitlab-ci.yml` -- GitLab CI

If a pipeline already exists, extend it rather than replacing it.

### Phase 3: Generate Pipeline

Start with the minimal reliable baseline from [pipeline-templates.md](pipeline-templates.md):
1. Install dependencies (with caching)
2. Run linter/formatter check
3. Run tests
4. Build (if applicable)

Use the detected runtime version. Pin action versions to specific SHAs or major versions. Use lockfile-based caching.

### Phase 4: Validate

Before presenting the pipeline to the user:
- Verify all referenced tools are in the project's dependencies
- Check that test/lint/build commands match the project's configuration
- Ensure secrets are referenced by name, not hardcoded
- Confirm the runner OS matches the project's requirements

### Phase 5: Add Deployment Stages

Only if the user requests deployment. Add stages for:
- Staging deployment (on merge to main)
- Production deployment (on tag or manual trigger)
- Environment-specific secrets and approvals

Keep deployment stages separate from CI stages. CI should pass before deployment is attempted.

## Rules

- Always cache dependencies. Uncached CI is a waste of compute.
- Pin versions: actions, runtimes, dependencies. Floating versions cause flaky builds.
- Keep pipelines under 10 minutes. If slower, parallelize or split.
- Never store secrets in pipeline files. Use the platform's secrets manager.
- Run the full test suite, not a subset. Partial CI is worse than no CI.

## Sub-files

| File | Topic |
|------|-------|
| [stack-detection.md](stack-detection.md) | File signals per ecosystem |
| [pipeline-templates.md](pipeline-templates.md) | GitHub Actions and GitLab CI scaffolds |
