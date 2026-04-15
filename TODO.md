# TODO

## Session log

**2026-04-12** -- Scribe agent. 51 skills, 8 agents + shared, 733 tests, 0 lint errors.

- New agent: scribe -- session insight extractor that closes the knowledge loop
- Two-phase watch: tails ~/.claude/history.jsonl for session discovery, reads full session JSONL (~/.claude/projects/{key}/{sid}.jsonl) for rich data (tool calls, file edits, bash commands)
- Session analysis: tool usage profiling, files touched, commands run, correction detection, preference detection
- Enhanced classification beyond recall extract: correction (user correcting Claude), preference ("I prefer X"), decision, gotcha + tool usage patterns (edits without tests, exploration sessions)
- Deduplication: FTS5 search + Jaccard token overlap against existing recall entries before writing
- AARTS hooks: PreScribeWrite (min length, noise filtering) + recall's PreMemoryWrite (injection/credential scanning via Store.add)
- Idle detection: sessions with no new messages for N minutes get analyzed
- CLI: watch (--once, --idle-minutes), analyze (--dry-run), stats, recent, serve
- MCP: 3 tools (scribe_status, scribe_stats, scribe_recent)
- Activity log at ~/.local/share/scribe/activity.jsonl
- 114 tests, 0 mocks, 0 lint errors
- Live verified on real sessions: correctly extracts corrections, decisions, gotchas from natural language; produces 0 noise from clean coding sessions

**2026-04-12** -- Proactive trigger wiring. 51 skills, 7 agents + shared, 619 tests, 0 lint errors.

- Created agents/shared/ package: paths.py (XDG alert log paths), notify.py (generic JSONL append + macOS notifications), 11 tests
- Sentinel: standardized alert log to ~/.local/share/sentinel/alerts.jsonl (was CWD-relative), added --notify flag to check/watch commands
- Watchdog: WatchdogAlert model, alerts_from_health() converts WARN/FAIL checks, JSONL persistence to ~/.local/share/watchdog/alerts.jsonl, `alerts` CLI command, --notify flag, 8 new tests
- Digest: notifier.py uses shared paths (same value, consistent import)
- Prepper watch: cross-agent alert poller with byte-offset tracking, TOML config, macOS notification dispatch, unified log at ~/.local/share/prepper/alerts.jsonl, 17 new tests
- Prepper CLI: `watch` command (--config, --interval, --once), `alerts` command (--agent filter, rich table)
- prepper_alerts MCP tool: unified cross-agent alert view with agent filter, fallback to individual logs
- gather_watchdog_alerts() gatherer wired into briefing assembly
- Prepper MCP tools: 3 (was 2, added prepper_alerts)
- All 5 agents use shared.paths for standard XDG alert locations
- Data flow: sentinel/watchdog/digest -> JSONL logs -> prepper watch -> unified log + macOS notifications

**2026-04-12** -- AARTS Phase 2 hooks. 51 skills, 7 agents, 583 tests, 0 lint errors.

- AARTS Level 2 hooks: PostToolUse (digest), PreMemoryRead (prepper), PreSubAgentSpawn (autoresearch)
- digest hooks.py: scan adapter response items (title, url, raw dict) for injection patterns before synthesis; sanitize recall_context strings; strip poisoned items, log removals
- prepper hooks.py: scan recall entries before briefing injection, strip entries with injection patterns, flag auto-sourced entries (digest:/extract:) with [auto] provenance prefix
- autoresearch hooks.py: pre_sub_agent_spawn validates file changes against mutable_files + scans content for dangerous patterns (os.system, subprocess, eval, exec, __import__); replaces silent skip with formal DENY
- ASK verdict enforcement: log_hook_result() added to all 5 agents (recall, autoresearch, patchbot, digest, prepper); ASK verdicts now log warning to stderr instead of passing silently
- Fixed prepper gatherers.py: RecallStore -> Store import, added SearchResult unwrapping
- Hooks wired into enforcement points: pipeline.py (digest), gatherers.py (prepper), cli.py (autoresearch), store.py (recall), runner.py (autoresearch), updater.py (patchbot)
- 63 new hook tests (25 digest + 17 prepper + 15 autoresearch + 3 patchbot + 3 recall), all passing, 0 mocks

**2026-04-12** -- Skill extraction sprint. 51 skills, 7 agents, 520 tests, 0 lint errors.

- Scraped travisvn/awesome-claude-skills for gap analysis (28 community skills catalogued)
- 4 new skills from gap analysis:
  - playwright: browser automation + testing (Python + TS), selectors, waiting, accessibility, automation recipes
  - security-audit: OWASP Top 10, variant analysis (Trail of Bits), static analysis (semgrep), supply chain
  - skill-creator: interactive scaffolding, frontmatter templates, quality checklist + anti-patterns
  - web-asset-generator: favicons, app icons (iOS/Android/PWA), devicons, OG/social images, image optimization
- Prepper: gather_watchdog_health() surfaces repo failures/warnings in briefings
- Recall: MAD-normalized relevance floor, adaptive search filtering
- Prepper: token budget + task-hint for briefing assembly
- LLM cost optimizer: cross-agent context management technique
- Lint/format fixes across all 7 agents
- Sage statusline integration (suppress nag, preserve custom statusline)

**2026-04-12** -- AARTS Phase 1 hooks. 47 skills, 7 agents, 520 tests, 0 lint errors.

- AARTS Level 1 hooks: PreToolUse (autoresearch, patchbot), PreMemoryWrite (recall)
- autoresearch hooks.py: verify/guard command allowlist (cargo test, pytest, nargo, mix, go, make, just) + denylist (curl, wget, ssh, sudo, eval, pip/npm/cargo install)
- patchbot hooks.py: allowlist derived from detector.py commands (outdated/update/test per ecosystem) + git/gh for PR creation, denylist (force push, reset --hard, curl, sudo)
- recall hooks.py: injection pattern scanning (XML tags, instruction delimiters, role reassignment, override attempts) + credential detection (API keys, tokens, AWS keys, private keys, bearer tokens)
- Hooks wired into enforcement points: runner.py (autoresearch), updater.py (patchbot), store.py (recall)
- Shared HookResult model (verdict: allow/deny/ask, hook name, reason) -- same pattern across all 3 agents
- Digest watch TOML example config shipped (digest-watch.example.toml)
- 73 new hook tests (21 autoresearch + 29 patchbot + 23 recall), all passing, 0 mocks

**2026-04-12** -- Digest proactive mode. 47 skills, 7 agents, 448 tests, 0 lint errors.

- Digest alert thresholds: engagement floor, credibility tier filter, new items count, accelerating count (19 tests)
- Digest trigger rules: Snapshot governance proposals (active/pending), dependency engagement spikes (configurable factor)
- Notification dispatch: macOS native via osascript + terminal-notifier, JSONL alert log at ~/.local/share/digest/alerts.jsonl (8 tests)
- Watch loop: TOML config with per-topic thresholds/triggers, configurable synthesis on/off, poll interval (7 tests)
- CLI: `digest watch --config <toml> [--once]`, `digest alerts [--limit N]`
- MCP: `digest_alerts` tool (7 MCP tools total, up from 6)
- Prepper: `gather_digest_alerts()` gatherer reads digest alert log (HIGH priority section)
- All surfaces updated: alerts.py, notifier.py, watcher.py, cli.py, mcp_server.py, prepper gatherers/briefing

**2026-04-12** -- Latent Briefing integration. 47 skills, 7 agents, 409 tests, 0 lint errors.

- Applied insights from Latent Briefing paper (Ramp Labs, Ben Geist) to agent context management
- Recall: MAD-normalized relevance floor (`--min-relevance`) for adaptive search filtering (4 tests)
- Prepper: token budget (`--budget`) drops LOW sections first, truncates MEDIUM, never drops HIGH (4 tests)
- Prepper: task-hint (`--task`) boosts MEDIUM sections matching consumer task terms (2 tests)
- LLM cost optimizer: added technique #7 "Cross-Agent Context Management" (relevance floors, task-guided selection, adaptive budgets)
- Paper stored as recall insight for future reference
- All surfaces updated: Store.search(), recall CLI/MCP, prepper CLI/MCP

**2026-04-11** -- Integration sprint. 47 skills, 7 agents, 399 tests, 0 lint errors.

- CoinGecko MCP server documented (remote keyless + local stdio options)
- CoinGecko digest adapter: trending tokens, gainers/losers, new listings (7 tests)
- Blockscout digest adapter: on-chain token transfers, address activity (8 tests)
- Differential digests: SQLite feed memory, new/ongoing/accelerating/declining classification (15 tests)
- Prepper SessionStart hook: auto-inject briefing at session start (script + settings.json docs)
- Cross-agent composition: prepper now gathers sentinel alerts + digest history
- MCP server tests: 21 tests across all 7 agents (3 per server factory)
- Skill trigger accuracy harness: 37 snapshot tests, keyword-based, covers all categories
- Polymarket Gamma API verified working
- Snyk agent-scan blocked on SNYK_TOKEN (needs `snyk auth`)
- New skills: `coingecko` (4 ref files), `blockscout` (16-tool reference)
- Sentinel expanded: +3 chains (Celo, Mode, Neon EVM/Solana)
- Solana/Tron support via CoinGecko platform IDs + Neon EVM bridge
- Source credibility scoring: 3-tier model (verified/deliberate/passive), per-item bonuses (18 tests)
- Structured output views: timeline, controversy map, tag trends, source breakdown (11 tests)
- Test gap coverage: sentinel monitor, digest dedup, patchbot parser, prepper gatherers (44 tests)
- All 7 agents pip-installed, ~/.mcp.json configured via chezmoi (7 agents + coingecko)
- Source credibility tracking over time: per-source hit/miss across digests, 0.5-1.5 accuracy multiplier (14 tests)
- Digest <-> recall bridge: store highlights as recall entries, fetch historical context for synthesis (10 tests)
- Digest MCP tools now at 6 (added digest_recall_context, digest_store_to_recall)

**2026-04-11** -- Agent <-> skill MCP integration. All 7 agents now expose MCP servers via `<agent> serve`. 45 skills, 7 agents, 253 tests, 0 lint errors.

- All 8 agents now have `mcp_server.py` + `serve` CLI command (FastMCP, stdio transport)
- 5 new agent skill stubs: autoresearch, watchdog, prepper, sentinel, patchbot
- Updated digest skill with MCP section, recall already had it
- 31 MCP tools total across all agents (8 recall + 7 digest + 3 scribe + 3 autoresearch + 2 watchdog + 3 prepper + 2 sentinel + 3 patchbot)

**2026-04-11** -- All phases (1-7) complete. 40 skills, 7 agents, 253 tests, 0 lint errors.

- Ruff lint + format pass: all 7 agents at 0 errors.
- Phase 7: 5 agents shipped (autoresearch, watchdog, prepper, sentinel, patchbot).
- Distribution: .claude-plugin/plugin.json + marketplace.json, npx skills CLI, chezmoi, manual.
- Phase 6: 20 skill extractions (8 Tier 1 + 12 Tier 2). 40 skills total.
- Phase 5: Recall agent MVP + auto-extraction + digest web3 adapters + skill wiring.
- Polymath v2.0.0: three-tier roster, polymath persona composition, roster caching.
- Phase 4: 5 merged skill extractions (tdd, code-review, mcp-server-builder, prd-to-plan, prd-to-issues).
- Phase 3: digest adapters (HN, GitHub, Reddit, YouTube + ethresear.ch, Snapshot, Polymarket, packages).
- Snyk agent-scan: uv + snyk installed, auth done. Analysis server returning 503 (retry later).

**2026-04-10** -- Phases 1 + 2 + most of Phase 3 landed.

- Claude-api SKILL.md split 283 -> 89 lines; extracted `shared/surfaces.md`, `shared/thinking-effort.md`, `shared/pitfalls.md`
- 3 new skills extracted: `grill-me`, `git-guardrails` (with executable hook script), `env-secrets-manager` (+ 2 reference files)
- 13 skills total, all passing `./scripts/skills-lint.sh`
- Digest agent MVP shipped: HN + GitHub adapters, engagement-weighted ranking with GitHub star cap, cross-platform dedup, Claude synthesis via Opus 4.6 adaptive thinking, typer CLI with markdown/terminal output, query expansion with platform-specific terms
- 24 unit tests, 0 mocks, all passing
- Live verified with "noir zero knowledge" (100% signal) and "claude code skills" (surfaced the ecosystem)
- Snyk scan deferred (needs `uv` installed); live Claude synthesis blocked on API credit balance (`--no-synthesis` flag added as workaround)

**New skill extraction candidates discovered via digest:**

- `travisvn/awesome-claude-skills` -- curated list, scrape for more candidates
- `thedotmack/claude-mem` -- session memory plugin, directly relevant to recall agent design
- `wshobson/agents` -- multi-agent orchestration patterns
- `maxritter/pilot-shell` -- spec-driven plans, enforced quality gates
- `vibeeval/vibecosystem` -- 139 agents + 283 skills, study for patterns
- `uditgoenka/autoresearch` + `drivelineresearch/autoresearch-claude-code` -- autoresearch ports, cross-reference before our own autoresearch impl
- `mcpware/claude-code-organizer` -- dashboard for configs, worth evaluating

---

## Execution Plan

Phases are sequential but produce usable output at each step. Skills and agents interleave.

### Phase 1: Warmup & Cleanup (skills)

- [x] Split claude-api SKILL.md (283 -> 89 lines + surfaces.md, thinking-effort.md, pitfalls.md)
- [x] Ensure all sub-files have complete frontmatter (all 101 sub-files have impact, impactDescription, tags)
- [x] Audit naming consistency across all skills (all kebab-case, consistent)
- [x] Review cross-references (all verified, no broken refs)
- [ ] Run snyk/agent-scan against existing skills (uv + snyk installed, auth done, analysis server returning 503 -- retry later)

### Phase 2: Quick Skill Extractions

- [x] `grill-me` -- interview skill adapted from [mattpocock/skills](https://github.com/mattpocock/skills)
- [x] `git-guardrails` -- PreToolUse hooks + block-dangerous-git.sh from [mattpocock/skills](https://github.com/mattpocock/skills)
- [x] `env-secrets-manager` -- leak detection, rotation, pre-commit setup from [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills)

### Phase 3: Digest Agent MVP

Multi-platform activity digest. Our version of [last30days-skill](https://github.com/mvanhorn/last30days-skill).

**Core idea:** Topic in -> synthesized brief out, weighted by credibility signals. Differential by default -- highlights what changed, not just what exists.

- [x] Scaffold agent structure (agents/digest/, pyproject.toml, typer CLI)
- [x] Platform adapters (common interface, one module per source)
  - [x] Hacker News (Algolia API, no auth) -- live tested
  - [x] GitHub (gh CLI, repos + issues) -- live tested
  - [x] Reddit (public search JSON API, no OAuth) -- unit tested
  - [ ] X (deferred: free API tier eliminated, nitter dead, Basic tier $100/mo)
  - [x] YouTube (yt-dlp flat-playlist search, no API key) -- unit tested
- [x] Query expansion -- static rules in expansion.py, substring matching, platform-specific `hn_terms`, GitHub `org:`/`repo:`/`topic:` qualifiers routed to `gh` CLI flags. LLM-based expansion deferred as future extension.
- [x] Ranking algorithm: log-weighted engagement + recency decay, per-platform weights
- [x] Cross-platform deduplication (URL normalization + title similarity via SequenceMatcher)
- [x] Claude synthesis step: raw data -> narrative with citations (code done, live test blocked on API credits as of 2026-04-10 -- `--no-synthesis` flag added as workaround)
- [x] CLI entry point: `digest generate <topic> [--days 30] [--platforms hn,github]`
- [x] Output formats: markdown (file), rich/terminal

### Phase 4: Merged Skill Extractions

Bigger extractions needing adaptation/merging. Interleaved with digest polish.

- [x] `tdd` -- merged mattpocock (workflow, vertical slices, deep-modules, interface-design) + alirezarezvani (mutation testing, polyglot). 7 files, Elixir/Go/Rust/Python/TS examples
- [x] `code-review` -- merged pr-review-expert (blast radius, security, 40-item checklist) + code-reviewer (SOLID violations, quality scoring). 6 files
- [x] `mcp-server-builder` -- OpenAPI -> MCP server scaffolding (Python FastMCP + TS). Auth/safety, validation, testing. 5 files
- [x] `prd-to-plan` -- PRD -> phased tracer-bullet vertical slices. Plan file to `./plans/`. 3 files
- [x] `prd-to-issues` -- PRD -> GitHub issues with HITL/AFK distinction, dependency ordering. 3 files

### Phase 5: Recall Agent + Digest Phase 2

Knowledge capture and retrieval. Our version of [paperclip](https://github.com/paperclipai/paperclip).

**Key difference from paperclip:** We don't need the full org-chart/multi-agent orchestration. We want the knowledge capture loop -- watch sessions, extract insights, make them findable.

**Key insight:** recall captures _after_ sessions, prepper (Phase 7) prepares _before_. Together they close the knowledge loop.

- [x] **Recall agent MVP**
  - [x] Define knowledge schema (5 types: decision, pattern, gotcha, link, insight)
  - [x] Storage backend: local SQLite with FTS5 (porter stemming, WAL mode, trigger-synced index)
  - [x] Capture interface: CLI `recall add "insight" --type gotcha --project X --tags a,b`
  - [x] Query interface: `recall search "topic"` with FTS5 ranking, project/type/tag filters
  - [x] Auto-extraction: parse `~/.claude/history.jsonl` for decision-indicating patterns, classify by type, extract tags, CLI `recall extract --days 30 --dry-run`
  - [x] Tag/categorize by project, topic, date
  - [x] Integration: FastMCP server with 8 tools (add, search, list, get, delete, stats, stale, extract)
  - [x] Prune/decay: `recall stale --days 90` surfaces entries not accessed recently
- [x] **Digest Phase 2: Web3-native sources**
  - [ ] Farcaster (deferred: Neynar API requires paid subscription, no free tier)
  - [x] ethresear.ch (Discourse search JSON API, no auth) -- engagement: views + likes*5 + posts*3
  - [x] Snapshot governance (GraphQL API, no auth) -- engagement: votes + scores_total, space: qualifiers
  - [x] Blockscout -- on-chain activity digest adapter (Blockscout API v2, token transfers + address txs)
  - [x] Prediction markets: Polymarket Gamma API (no auth) -- engagement: volume traded
  - [x] Package registries: hex.pm + crates.io + npm (all no auth) -- engagement: recent downloads
- [x] Wire `/digest` slash command skill (skills/digest/SKILL.md)
- [x] Wire recall context skill (skills/recall/SKILL.md)

### Phase 6: Remaining Extractions + Distribution

- [x] **Remaining skill extractions (Tier 1)**
  - [x] `design-an-interface` -- "Design It Twice" (Ousterhout), parallel sub-agents with divergent constraints. 3 files.
  - [x] `triage-issue` -- Bug investigation -> GitHub issue with TDD fix plan, durability rules. 2 files.
  - [x] `dependency-auditor` -- Multi-language vuln scanning + license compliance (JS/Python/Go/Rust/Ruby/Elixir/Java). 3 files.
  - [x] `ci-cd-pipeline-builder` -- Stack detection -> GitHub Actions/GitLab CI generation. 3 files.
  - [x] `tech-debt-tracker` -- Debt scanning, cost-of-delay prioritization, trend dashboards. 3 files.
  - [x] `release` -- Merged release-manager + changelog-generator. Conventional commits, semver, readiness checks. 4 files.
  - [x] `observability-designer` -- SLO/SLI design, burn rate alerting, dashboard generation. 4 files.
  - [x] `agent-designer` -- Multi-agent architecture patterns, tool schemas, guardrails. 4 files.
- [x] **Tier 2 extractions**
  - [x] `ubiquitous-language` -- DDD glossary extraction, canonical terms, UBIQUITOUS_LANGUAGE.md output. 1 file.
  - [x] `architect` -- Merged senior-architect + improve-codebase-architecture. ADR workflows, dependency classification, pattern detection. 3 files.
  - [x] `qa` -- Interactive QA with background explorer agent, scope assessment, issue filing. 1 file.
  - [x] `focused-fix` -- 5-phase bug fix (SCOPE->TRACE->DIAGNOSE->FIX->VERIFY), 3-strike architecture check. 2 files.
  - [x] `git-worktree-manager` -- Parallel dev with deterministic port allocation. 2 files.
  - [x] `database-designer` -- Schema analysis, ERD generation, index optimization, migration safety. 4 files.
  - [x] `performance-profiler` -- Polyglot profiling (Node/Python/Go/Elixir/Rust), optimization checklist. 3 files.
  - [x] `codebase-onboarding` -- Auto-generate onboarding docs, audience-aware (junior/senior/contractor). 1 file.
  - [x] `adversarial-reviewer` -- Three personas (Saboteur/New Hire/Security Auditor), mandatory findings. 2 files.
  - [x] `self-improving-agent` -- Auto-memory curation, pattern promotion lifecycle. 2 files.
  - [x] `rag-architect` -- RAG pipeline design, chunking/embedding/retrieval/evaluation. 3 files.
  - [x] `llm-cost-optimizer` -- 7 optimization techniques in priority order, proactive triggers. 2 files.
- [x] **Distribution**
  - [x] Add `.claude-plugin/marketplace.json` + `plugin.json` (self-listing pattern)
  - [x] Keep chezmoi `.chezmoiexternal.toml` method (updated to main branch, 168h refresh)
  - [x] Support `npx skills@latest add DROOdotFOO/agent-skills` method
  - [x] Document all installation paths in README (plugin, npx, chezmoi, manual)

### Phase 7: Advanced Agents

- [x] **Autoresearch** -- Domain-agnostic autonomous experiment runner. Generalizes beyond ML to Noir circuits, Solidity gas, compiler passes.
  - [x] Domain-agnostic harness: configurable verify command + metric pattern + mutable files
  - [x] Single optimization metric per experiment with direction (lower/higher)
  - [x] Fixed time budget per run (default 5 min, tunable via --budget)
  - [x] JSONL experiment tracker: config + run results (metric, status, commit, duration)
  - [x] Agent prompt design: objective + current best + results history + mutable file contents -> ONE focused change
  - [x] Guard command support (optional safety check, e.g. `cargo test`)
  - [x] Results dashboard: markdown table with deltas from baseline
  - [x] Git-as-memory: branch per experiment, keep/discard via commit/revert
  - [ ] Safety: sandbox execution, resource limits, no network during training (deferred)
  - [ ] mini-axol deployment: systemd service or cron, overnight batch mode (deferred)

  **Tech:** Python (typer, pydantic, anthropic). 33 tests, all passing.

- [x] **Watchdog** -- Continuous repo health monitor. 6 checks (stale PRs, CI status, issue age, TODO-closed-refs, lockfile audit, security advisories). TOML config, markdown reports, continuous watch mode. 21 tests.

- [x] **Prepper** -- Pre-session context builder. 7 gatherers (git activity, GitHub state, dependency status, recall, CI status, sentinel alerts, digest history). SessionStart hook. 17 tests.

- [x] **Sentinel** -- On-chain contract monitor. 4 alert rules (large transfers, ownership changes, unusual methods, selfdestruct). Blockscout API v2, 11 chains supported, TOML watchlist config, JSONL alert log. 51 tests.

- [x] **Patchbot** -- Polyglot dependency updater. 5 ecosystems (Elixir, Rust, Node, Go, Python). Detects from lockfiles, runs outdated checks, updates + tests, creates PRs via gh CLI. 33 tests.

---

## Deferred / Ongoing

### Digest advanced phases (after Phase 5)

**Phase 3: Differential digests + feed memory**

- [x] Feed memory (sqlite): store past digests, track narrative arcs over time
- [x] Differential mode: "new since last digest" vs "ongoing, declining" vs "new and accelerating"
- [x] Source credibility tracking: per-source hit/miss tracking across digests, accuracy multiplier (0.5-1.5)
- [x] Credibility layering: prediction market odds > engagement metrics > raw volume (3-tier model)

**Phase 4: Proactive mode**

- [x] Watch mode: `digest watch --config <toml>` with per-topic TOML config, configurable poll interval, `--once` flag
- [x] Alert thresholds: engagement floor, credibility tier filter, new items count, accelerating count -> macOS notifications (osascript + terminal-notifier) + JSONL alert log
- [x] Triggers: Snapshot governance proposals (active/pending), dependency engagement spikes (configurable factor)
- [ ] Overlap with watchdog: digest watches the world, watchdog watches your repos

**Phase 5: Structured output + integrations**

- [x] MCP server mode: `digest serve` with 7 tools (generate, list_platforms, expand_query, structured_view, recall_context, store_to_recall, alerts)
- [x] Structured output: controversy map, timeline view, tag trends, source breakdown (`--view` flag + MCP tool)
- [x] prepper integration: prepper gathers digest history + sentinel alerts into briefings
- [x] recall integration: digest <-> recall bridge (store highlights, fetch historical context for synthesis)
- [x] sentinel integration: on-chain events flow via blockscout digest adapter + prepper sentinel gatherer

### Agent security

**[snyk/agent-scan](https://github.com/snyk/agent-scan)** -- Security scanner for MCP servers, skills, and agent harnesses. Catches prompt injection, tool shadowing, malicious code, credential leaks, toxic flows.

- [ ] Run `uvx snyk-agent-scan@latest --skills ./skills/` against our skills (Phase 1)
- [ ] Add to CI: `uvx snyk-agent-scan@latest --ci --json --skills`
- [ ] Evaluate `guard install claude` for real-time PreToolUse hooks
- [ ] Consider MCP server mode for agent self-scanning (digest, recall, autoresearch)

**[Gen Digital Agent Trust Hub](https://ai.gendigital.com/agent-trust-hub)** -- AARTS (AI Agent Runtime Safety Standard): 19 hook points for runtime security. [github.com/gendigitalinc/aarts](https://github.com/gendigitalinc/aarts)

- [x] Study AARTS hook point model as design checklist for our agents (see handover below)
  - digest: PreMCPConnect (external data sources), PostToolUse (injection via adapter responses)
  - recall: PreMemoryWrite/Read (knowledge base poisoning), PostToolUse (injection via search results)
  - autoresearch: PreToolUse/shell (training commands), PreSubAgentSpawn (experiment isolation)
  - sentinel/watchdog: PreMCPConnect (Blockscout/GitHub API), PostToolUse (response validation)
  - prepper: PreCompact (briefing context integrity), PreMemoryRead (recall poisoning)
  - patchbot: PreToolUse/shell (dependency update commands), package supply chain (T005)
- [x] Evaluate Sage ADR engine for Claude Code runtime protection (see docs/aarts-handover.md)
  - Install: `/plugin marketplace add https://github.com/gendigitalinc/sage.git` then `/plugin install sage@sage`
  - v0.8.0 (Apr 2026): URL reputation, local heuristic threat rules, supply-chain package checks, plugin scanning
  - Covers PreToolUse (shell/file/URL) but MCP tool interception (`mcp__*`) NOT yet implemented
  - Privacy: file content stays local, only URL/package hashes sent to Gen Digital APIs (can disable for offline)
  - Verdict: install now for shell/URL/supply-chain coverage; wait for MCP interception before relying on it for our MCP agents
- [x] AARTS Phase 1 (Level 1) implementation: PreToolUse + PreMemoryWrite hooks
  - autoresearch: PreToolUse validates verify/guard commands against allowlist (73 tests)
  - patchbot: PreToolUse validates outdated/update/test/git/gh commands against allowlist
  - recall: PreMemoryWrite scans for injection patterns + credential strings before SQLite INSERT
  - Shared HookResult model (verdict: allow/deny/ask) -- same interface across all 3 agents
  - Hooks enforced at subprocess call sites (runner.py, updater.py, store.py)
  - Digest watch TOML example config shipped (digest-watch.example.toml)
- [x] AARTS Phase 2 (Level 2): PostToolUse (digest adapters), PreSubAgentSpawn (autoresearch), PreMemoryRead (prepper)
- [ ] Evaluate Skill IDs ([github.com/gendigitalinc/skill-id-standard](https://github.com/gendigitalinc/skill-id-standard)) for skill integrity verification between chezmoi apply runs

**Note:** AARTS is v0.1 draft, Sage is v0.8.0, Skill ID signing is a proposal. Early but worth tracking.

### Agent <-> skill integration

Skills that invoke or surface agent capabilities inside Claude Code sessions:

- [x] All 7 agents expose MCP servers via `<agent> serve` (stdio transport, FastMCP)
- [x] 5 new agent skill stubs (autoresearch, watchdog, prepper, sentinel, patchbot)
- [x] Updated digest skill with MCP config section
- [x] recall already had MCP server + skill docs
- [x] `prepper` SessionStart hook (scripts/hooks/prepper-session-start.sh + settings.json docs)
- [x] Proactive triggers: sentinel alerts + watchdog degradation -> prepper watch -> macOS notifications + unified alert log

### Skills structural patterns (apply as we go)

Lessons from [mattpocock/skills](https://github.com/mattpocock/skills) and [slavingia/skills](https://github.com/slavingia/skills):

- [ ] Keep SKILL.md under 100 lines, split depth into companion files
- [ ] Add workflow/procedure skills alongside reference skills
- [ ] **Output sections** -- every skill specifies what artifact the user gets
- [ ] **Anti-patterns as first-class content** -- "WRONG" examples alongside correct
- [ ] **argument-hint frontmatter** -- for advisory/meta skills that take freeform input
- [ ] Consider `.claude-plugin/` marketplace format for distribution

### Testing strategy

- [x] Skill trigger accuracy harness: `scripts/skill-triggers-test.py` (37 snapshot tests)
- [x] MCP server factory tests: 21 tests across all 7 agents
- [x] Test gap coverage: sentinel monitor, digest dedup, patchbot parser, prepper gatherers
- [ ] Evaluate snyk/agent-scan as a safety gate (blocked: snyk maintenance)

### Research backlog

- [ ] Review alirezarezvani marketing/PM skills for hidden gems (manual pass)
- [ ] Watch for new skills repos in Claude Code ecosystem
- [ ] Evaluate [obra/superpowers-marketplace](https://github.com/obra/superpowers-marketplace) for overlap
- [ ] Track AARTS spec evolution (currently v0.1)
- [ ] Track Sage MCP interception support (not in v0.8.0, critical for our 7 MCP agents)

---

### Digest: Research / Medical / Legal / Security adapters

New platform adapters to expand digest beyond tech/crypto. Prioritized by API quality, signal richness, and breadth. Full API specs in `agents/digest/SPECS.md`.

Each adapter touches 5 files: `adapters/{key}.py`, `adapters/__init__.py`, `credibility.py`, `ranking.py`, `tests/test_{key}.py`. Optionally `expansion.py` for domain-specific query fields.

**Tier 1 -- High value, clean APIs (implement first)**

- [ ] Semantic Scholar (`semanticscholar`) -- T1. JSON, 1 RPS. Best engagement signals: citationCount, influentialCitationCount, citationVelocity, TLDR summaries. Covers SSRN content via externalIds. Key optional (S2_API_KEY). Weight 2.5, DELIBERATE.
- [ ] PubMed (`pubmed`) -- T1. JSON (esearch/esummary) + XML (efetch). Two-step: esearch for PMIDs, esummary for metadata. Enrich via iCite API for citation_count + relative_citation_ratio. Key optional (NCBI_API_KEY, 10 req/s). Pairs with cancer-predisposition skill. Weight 2.5, DELIBERATE.
- [ ] Federal Register (`federalregister`) -- T1. JSON, keyless, generous limits. comment_count + significant flag for engagement. Easiest legal API. Weight 1.2, VERIFIED.
- [ ] Shodan enhancements -- T1, low effort (existing adapter):
  - [ ] InternetDB fallback (`https://internetdb.shodan.io/{ip}`) -- free, keyless, weekly-refresh port/vuln data
  - [ ] Facets endpoint (`/shodan/host/count?facets=...`) -- free, unlimited, zero query credits
  - [ ] Exploits API (`https://exploits.shodan.io/api/search`) -- separate base URL, CVE/ExploitDB/Metasploit

**Tier 2 -- Good value, moderate complexity**

- [ ] arXiv (`arxiv`) -- T2. Atom XML (needs xml.etree parser). **No engagement data** -- must composite with Semantic Scholar batch endpoint for citations. 1 req/3s rate limit (hard, must sleep). Keyless. Weight 2.0, DELIBERATE.
- [ ] OpenAlex (`openalex`) -- T2. JSON, 470M+ works (broadest coverage). cited_by_count + fwci (field-weighted citation impact). Routes SSRN via title/DOI search. Requires email for polite pool (OPENALEX_EMAIL). 100k credits/day. Weight 2.0, DELIBERATE.
- [ ] CourtListener (`courtlistener`) -- T2. JSON, clean API. citeCount for engagement, court hierarchy for credibility bonus. Free token required (COURTLISTENER_TOKEN). 5000 req/hr. Weight 2.0, DELIBERATE.
- [ ] ClinicalTrials.gov (`clinicaltrials`) -- T2. JSON, deeply nested under `protocolSection`. enrollment + phase for engagement. VERIFIED tier (real enrolled patients). Keyless, ~50 req/min. Weight 1.5.
- [ ] Congress.gov (`congress`) -- T2. JSON (append `&format=json`, default is XML!). Cosponsor count needs second API call per bill. Free key required (CONGRESS_API_KEY). 5000 req/hr. Weight 1.5, DELIBERATE.

**Tier 3 -- Niche or complex**

- [ ] Crossref (`crossref`) -- T3. JSON, is-referenced-by-count for citations. Secondary enrichment for DOI resolution, lower search quality than S2/OpenAlex. Polite pool via mailto (CROSSREF_EMAIL). Weight 1.5, DELIBERATE.
- [ ] regulations.gov (`regulations`) -- T3. JSON:API format (data/attributes nesting). numberOfCommentsReceived needs second call. Free key required (REGULATIONS_GOV_KEY). 1000 req/hr. Weight 1.5, DELIBERATE.
- [ ] openFDA (`openfda`) -- T3. JSON. Multiple sub-APIs (drug/event, drug/label, device/recall). Date format is YYYYMMDD not ISO. serious flag as quality signal. Key optional (OPENFDA_API_KEY). Weight 1.0, VERIFIED.
- [ ] bioRxiv/medRxiv (`biorxiv`) -- T3. JSON. **No search endpoint** -- date-range only, filter client-side. Prefer Semantic Scholar `venue:bioRxiv` filter for search. Keep native adapter for broad date scans. Keyless. Weight 0.8, PASSIVE.

**Tier 4 -- Complex format or low volume**

- [ ] WHO DON (`who`) -- T4. JSON (OData-style). No keyword search, HTML embedded in content fields. Low volume (few dozen/month). Best for watch/alert mode. Keyless. Weight 1.0, VERIFIED.
- [ ] CDC MMWR (`cdc`) -- T4. JSON + RSS. Irregular publication schedule. No engagement signals. Articles also indexed in PubMed (cross-adapter dedup). Keyless. Weight 0.8, VERIFIED.
- [ ] EUR-Lex (`eurlex`) -- T4. SPARQL queries against CDM ontology. 60s timeout, complex query construction. Citation graph via `cdm:work_cited_by`. Keyless. Weight 1.0, VERIFIED.
- [ ] UK Legislation (`uklegislation`) -- T4. Atom XML only (shares parser with arXiv). Effects count from `/changes/` sub-resource. Niche UK-focused. Keyless. Weight 0.8, VERIFIED.
- SSRN -- **no adapter needed**. No API exists. Route through OpenAlex (title/DOI search) or Semantic Scholar (externalIds.SSRN).

**Security**

- [x] Shodan -- REST API (SHODAN_API_KEY). Exposed hosts, services, CVEs, banner data. Adapter shipped.

**Shared infrastructure**

- [ ] XML parsing utility -- shared by arXiv (Atom), PubMed efetch (NCBI XML), UK Legislation (Atom). Extract to `adapters/_xml.py`.
- [ ] ExpandedQuery extensions -- add `arxiv_categories: list[str]`, `pubmed_mesh: list[str]`, `legal_jurisdiction: str` to `expansion.py`
- [ ] Credibility module updates -- add all new sources to SOURCE_TIERS + _per_item_bonus cases
- [ ] Ranking weights -- add all new adapter keys to PLATFORM_WEIGHTS

---

**Tech defaults:** Python (typer CLI, httpx, pydantic, sqlite3). MCP via FastMCP. Blockscout MCP for on-chain data. Deploy long-running agents to mini-axol (ansible roles ready).
