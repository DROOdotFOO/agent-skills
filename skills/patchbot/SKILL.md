---
name: patchbot
description: >
  Scan for outdated dependencies and update them across Elixir, Rust, Node, Go,
  and Python ecosystems.
  TRIGGER when: user asks about outdated dependencies, "update deps", "dependency
  check", "what needs updating", or invokes "/patchbot".
  DO NOT TRIGGER when: user is working on patchbot agent code itself.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: patchbot, dependencies, updates, security
---

# Patchbot

Polyglot dependency updater. Detects ecosystems from lockfiles, scans for outdated
packages, updates + tests, and optionally creates PRs.

## CLI Usage

```bash
# Detect ecosystems and list outdated deps
patchbot scan

# Filter to one ecosystem
patchbot scan --ecosystem rust

# Update and run tests
patchbot update --ecosystem node

# Update, test, and create a PR
patchbot pr --ecosystem elixir --base-branch main

# Dry run (preview only)
patchbot update --ecosystem python --dry-run
```

## Supported Ecosystems

| Ecosystem | Lockfiles | Update command | Test command |
|-----------|-----------|----------------|--------------|
| Elixir | mix.lock, mix.exs | `mix deps.update --all` | `mix test` |
| Rust | Cargo.lock, Cargo.toml | `cargo update` | `cargo test` |
| Node | package-lock.json, yarn.lock, pnpm-lock.yaml | `npm update` | `npm test` |
| Go | go.sum, go.mod | `go get -u ./...` | `go test ./...` |
| Python | requirements.txt, pyproject.toml, poetry.lock, uv.lock | `pip install --upgrade` | `pytest` |

## MCP Server

```bash
patchbot serve
```

### Configure MCP

Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "patchbot": {
      "command": "patchbot",
      "args": ["serve"]
    }
  }
}
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `patchbot_scan` | Detect ecosystems and list all outdated deps |
| `patchbot_outdated` | List outdated deps for a specific ecosystem |
| `patchbot_update` | Run update + tests for an ecosystem (dry_run by default) |

## Install

```bash
cd agents/patchbot
pip install -e .
```

Requires ecosystem-specific tooling (mix, cargo, npm, go, pip/pytest).
