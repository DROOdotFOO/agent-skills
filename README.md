# agent-skills

Claude Code skills for polyglot development, web3, ZK, UI/UX, and systems programming.

## Skills

| Skill | Description |
|-------|-------------|
| `claude-api` | Anthropic SDK reference (Python, TS, Go, Elixir, Rust, Lua, cURL) |
| `droo-stack` | Polyglot patterns (Elixir, TS, Go, Rust, C, Zig, Python, Lua, Shell, Noir, Chezmoi) |
| `raxol` | Elixir TUI/agent framework (TEA agents, MCP, headless sessions) |
| `noir` | ZK circuit design, Aztec contracts, constraint optimization |
| `solidity-audit` | Solidity dev standards, vulnerability taxonomy, Foundry-first audit |
| `ethskills` | Ethereum tooling, framework selection, EIP/ERC standards |
| `design-ux` | UI/UX design patterns, design tokens, accessibility, TUI aesthetics |
| `nix` | Nix language, flakes, NixOS, Home Manager, packaging |
| `native-code` | NIF development (C/Rust/Rustler), SIMD (Zig), BEAM native boundary |

## Installation

### With chezmoi (recommended)

Add to your `home/.chezmoiexternal.toml`:

```toml
[".agents/skills"]
    type = "archive"
    url = "https://github.com/Hydepwns/agent-skills/archive/v1.0.0.tar.gz"
    stripComponents = 2
    include = ["*/skills/**"]
    refreshPeriod = "0"
```

Then symlink to Claude Code's skills directory:

```bash
mkdir -p ~/.claude/skills
for d in ~/.agents/skills/*/; do
    ln -sf "../../.agents/skills/$(basename "$d")" ~/.claude/skills/
done
```

### Manual

```bash
git clone https://github.com/Hydepwns/agent-skills.git ~/.agents/skills-repo
ln -s ~/.agents/skills-repo/skills ~/.agents/skills
```

## Linting

```bash
./scripts/skills-lint.sh
```

Validates frontmatter, trigger clauses, file references, and cross-skill links.

## License

MIT
