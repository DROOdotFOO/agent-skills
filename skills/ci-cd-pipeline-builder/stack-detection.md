---
title: Stack Detection
impact: HIGH
impactDescription: Incorrect stack detection produces pipelines that fail on first run
tags: detection, ecosystems, manifests, lockfiles, languages
---

# Stack Detection

## File Signals by Ecosystem

### JavaScript / TypeScript

| Signal | Indicates |
|--------|-----------|
| `package.json` | Node.js project |
| `package-lock.json` | npm package manager |
| `yarn.lock` | Yarn package manager |
| `pnpm-lock.yaml` | pnpm package manager |
| `bun.lockb` | Bun runtime |
| `tsconfig.json` | TypeScript |
| `.eslintrc.*` / `eslint.config.*` | ESLint |
| `biome.json` | Biome (lint + format) |
| `prettier.config.*` / `.prettierrc*` | Prettier |
| `vitest.config.*` | Vitest test framework |
| `jest.config.*` | Jest test framework |
| `playwright.config.*` | Playwright E2E tests |
| `next.config.*` | Next.js framework |
| `vite.config.*` | Vite build tool |
| `turbo.json` | Turborepo monorepo |
| `nx.json` | Nx monorepo |

### Python

| Signal | Indicates |
|--------|-----------|
| `pyproject.toml` | Modern Python project |
| `setup.py` / `setup.cfg` | Legacy packaging |
| `requirements.txt` | pip dependencies |
| `poetry.lock` | Poetry package manager |
| `uv.lock` | uv package manager |
| `Pipfile` / `Pipfile.lock` | Pipenv |
| `pytest.ini` / `conftest.py` | pytest |
| `ruff.toml` / `[tool.ruff]` in pyproject.toml | Ruff linter |
| `mypy.ini` / `[tool.mypy]` | mypy type checker |
| `.python-version` | pyenv / mise version |

### Elixir

| Signal | Indicates |
|--------|-----------|
| `mix.exs` | Elixir project |
| `mix.lock` | Elixir dependencies |
| `.formatter.exs` | Elixir formatter config |
| `config/` dir with `.exs` files | Phoenix or release config |
| `lib/` + `test/` structure | Standard Mix project |
| `.tool-versions` / `.mise.toml` | Erlang/Elixir version management |

### Rust

| Signal | Indicates |
|--------|-----------|
| `Cargo.toml` | Rust project |
| `Cargo.lock` | Rust dependencies (commit for binaries, omit for libraries) |
| `rust-toolchain.toml` | Rust toolchain version |
| `clippy.toml` | Clippy linter config |
| `rustfmt.toml` | Rustfmt config |

### Go

| Signal | Indicates |
|--------|-----------|
| `go.mod` | Go module |
| `go.sum` | Go dependencies |
| `.golangci.yml` | golangci-lint config |
| `Makefile` with `go test` | Common Go build pattern |

### Solidity

| Signal | Indicates |
|--------|-----------|
| `foundry.toml` | Foundry project |
| `hardhat.config.*` | Hardhat project |
| `contracts/` dir with `.sol` files | Smart contract source |
| `remappings.txt` | Solidity import remappings |

### Ruby

| Signal | Indicates |
|--------|-----------|
| `Gemfile` | Ruby project |
| `Gemfile.lock` | Bundler dependencies |
| `.ruby-version` | Ruby version |
| `Rakefile` | Rake tasks |
| `.rspec` | RSpec test framework |

## Detecting Test Commands

Priority order for determining the test command:

1. Check `scripts.test` in `package.json` (Node)
2. Check for `pytest` in dependencies (Python)
3. Check for `mix test` (Elixir)
4. Check for `cargo test` (Rust)
5. Check for `go test ./...` (Go)
6. Check for `forge test` (Foundry/Solidity)
7. Check `Makefile` for a `test` target
8. Check `Rakefile` for test tasks (Ruby)

## Detecting Runtime Versions

Check these files in order:

1. `.tool-versions` (mise/asdf -- covers all runtimes)
2. `.mise.toml` (mise-specific)
3. `.node-version`, `.python-version`, `.ruby-version` (single-runtime files)
4. `rust-toolchain.toml` (Rust)
5. Engine fields in manifests (`engines.node` in package.json, `python_requires` in pyproject.toml)
6. Dockerfile `FROM` statements (fallback)

Use the detected version in the pipeline. If no version is detected, use the latest LTS/stable for the ecosystem.
