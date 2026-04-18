# patchbot

Polyglot dependency updater. Detects ecosystems in a repository, finds outdated dependencies, runs updates with test verification, and opens PRs via `gh`. Supports 5 ecosystems with AARTS PreToolUse hooks for command safety.

## Supported ecosystems

| Ecosystem | Lockfile detection | Outdated | Update | Test |
|-----------|-------------------|----------|--------|------|
| Elixir | `mix.lock` | `mix hex.outdated` | `mix deps.update` | `mix test` |
| Rust | `Cargo.lock` | `cargo outdated` | `cargo update` | `cargo test` |
| Node | `package-lock.json` | `npm outdated` | `npm update` | `npm test` |
| Go | `go.sum` | `go list -m -u all` | `go get -u` | `go test` |
| Python | `requirements.txt` | `pip list --outdated` | `pip install --upgrade` | `pytest` |

## Install

```bash
cd agents/patchbot && pip install -e ".[dev]"
```

## Usage

```bash
# Scan for outdated dependencies
patchbot scan --repo-path /path/to/repo
patchbot scan --ecosystem rust

# Update dependencies and run tests
patchbot update --repo-path /path/to/repo
patchbot update --ecosystem node --dry-run

# Update, test, and open a PR
patchbot pr --repo-path /path/to/repo --base-branch main
patchbot pr --ecosystem elixir --dry-run

# MCP server
patchbot serve
```

## How It Works

1. **Detection**: Scans for lockfiles (`mix.lock`, `Cargo.lock`, `package-lock.json`, `go.sum`, `requirements.txt`) to identify ecosystems
2. **Outdated check**: Runs ecosystem-specific outdated commands, parses output into structured results
3. **Update**: Runs update commands with AARTS PreToolUse hook validation (allowlist/denylist)
4. **Test**: Runs ecosystem test suite to verify updates don't break anything
5. **PR creation**: Creates a branch, commits changes, pushes, and opens a PR via `gh`

## MCP Server

```json
{"mcpServers": {"patchbot": {"command": "patchbot", "args": ["serve"]}}}
```

Tools: `patchbot_scan`, `patchbot_outdated`, `patchbot_update`

## Tests

```bash
python -m pytest tests/ -v   # 33 tests, 0 mocks
```
