---
title: Pipeline Templates
impact: CRITICAL
impactDescription: A bad pipeline template wastes developer time on every push and erodes trust in CI
tags: github-actions, gitlab-ci, templates, caching, matrix, deployment
---

# Pipeline Templates

## Principles

1. **Minimal first**: start with install, lint, test. Add stages only when needed.
2. **Cache aggressively**: restore dependencies from cache on every run.
3. **Pin versions**: actions, runtimes, and dependencies. Use lockfiles.
4. **Fail fast**: run the cheapest checks (lint, format) before expensive ones (test, build).
5. **Parallelize**: lint and test can run concurrently if they do not depend on each other.

## GitHub Actions: Node.js / TypeScript

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: '.node-version'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm test
```

## GitHub Actions: Python

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version-file: '.python-version'
          cache: 'pip'
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: pytest
```

## GitHub Actions: Elixir

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    env:
      MIX_ENV: test
    steps:
      - uses: actions/checkout@v4
      - uses: erlef/setup-beam@v1
        with:
          otp-version-file: '.tool-versions'
          elixir-version-file: '.tool-versions'
      - uses: actions/cache@v4
        with:
          path: |
            deps
            _build
          key: mix-${{ runner.os }}-${{ hashFiles('mix.lock') }}
          restore-keys: mix-${{ runner.os }}-
      - run: mix deps.get
      - run: mix format --check-formatted
      - run: mix compile --warnings-as-errors
      - run: mix test
```

## GitHub Actions: Rust

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy, rustfmt
      - uses: Swatinem/rust-cache@v2
      - run: cargo fmt --check
      - run: cargo clippy -- -D warnings
      - run: cargo test
```

## GitHub Actions: Go

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version-file: 'go.mod'
      - run: go vet ./...
      - run: golangci-lint run
      - run: go test -race ./...
```

## GitLab CI: Generic Pattern

```yaml
stages:
  - lint
  - test
  - build

variables:
  # Set ecosystem-specific cache paths

lint:
  stage: lint
  script:
    - # ecosystem-specific lint command

test:
  stage: test
  script:
    - # ecosystem-specific test command

build:
  stage: build
  script:
    - # ecosystem-specific build command
  only:
    - main
    - tags
```

## Advanced Patterns

### Dependency Caching

Always use lockfile hashes as cache keys. Restore keys allow partial cache hits when lockfiles change.

```yaml
# GitHub Actions pattern
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip  # or node_modules, deps, target, etc.
    key: ${{ runner.os }}-deps-${{ hashFiles('**/lockfile') }}
    restore-keys: ${{ runner.os }}-deps-
```

### Matrix Builds

Use matrix builds to test across multiple versions or platforms when the project supports them.

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest]
    version: ['18', '20', '22']  # Node versions, for example
  fail-fast: false  # do not cancel other jobs when one fails
```

### Deployment Stages

Add deployment only after CI passes. Use environments for approval gates.

```yaml
deploy-staging:
  needs: [ci]
  runs-on: ubuntu-latest
  environment: staging
  if: github.ref == 'refs/heads/main'
  steps:
    - uses: actions/checkout@v4
    - run: # deploy command

deploy-production:
  needs: [deploy-staging]
  runs-on: ubuntu-latest
  environment: production  # requires manual approval in GitHub settings
  if: startsWith(github.ref, 'refs/tags/')
  steps:
    - uses: actions/checkout@v4
    - run: # deploy command
```

### Monorepo: Path Filtering

Only run jobs when relevant files change.

```yaml
on:
  push:
    paths:
      - 'packages/api/**'
      - 'package.json'
      - '.github/workflows/api.yml'
```
