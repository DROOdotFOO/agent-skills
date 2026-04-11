# patchbot

Polyglot dependency updater. Detects ecosystems in a repository, finds outdated
dependencies, runs updates with test verification, and opens PRs via `gh`.

## Supported ecosystems

- Elixir (mix)
- Rust (cargo)
- Node (npm/yarn/pnpm)
- Go (go modules)
- Python (pip/poetry/uv)

## Install

```bash
pip install -e ".[dev]"
```

## Usage

Scan a repo for outdated dependencies:

```bash
patchbot scan --repo-path /path/to/repo
patchbot scan --ecosystem rust
```

Update dependencies and run tests:

```bash
patchbot update --repo-path /path/to/repo
patchbot update --ecosystem node --dry-run
```

Update, test, and open a PR:

```bash
patchbot pr --repo-path /path/to/repo --base-branch main
patchbot pr --ecosystem elixir --dry-run
```

## Polyglot scanning example

In a monorepo with `Cargo.toml`, `package.json`, and `go.mod`:

```
$ patchbot scan
Detected ecosystems: go, node, rust

go -- outdated dependencies
...

node -- outdated dependencies
...

rust -- outdated dependencies
...
```
