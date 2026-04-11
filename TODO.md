# TODO

## Session log

**2026-04-11** -- Integration sprint. 47 skills, 7 agents, 375 tests, 0 lint errors.

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

**2026-04-11** -- Agent <-> skill MCP integration. All 7 agents now expose MCP servers via `<agent> serve`. 45 skills, 7 agents, 253 tests, 0 lint errors.

- All 7 agents now have `mcp_server.py` + `serve` CLI command (FastMCP, stdio transport)
- 5 new agent skill stubs: autoresearch, watchdog, prepper, sentinel, patchbot
- Updated digest skill with MCP section, recall already had it
- 23 MCP tools total across all agents (8 recall + 3 digest + 3 autoresearch + 2 watchdog + 2 prepper + 2 sentinel + 3 patchbot)

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
  - [x] `llm-cost-optimizer` -- 6 optimization techniques in priority order, proactive triggers. 2 files.
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
- [ ] Source credibility scoring: track which sources were later proven wrong, downweight hype over time
- [x] Credibility layering: prediction market odds > engagement metrics > raw volume (3-tier model)

**Phase 4: Proactive mode**

- [ ] Watch mode: define topics of interest, run on schedule (cron/launchd)
- [ ] Alert thresholds: push notification when topic crosses engagement/credibility threshold
- [ ] Triggers: new governance proposal on watched contract, spike in discussion of a dependency, etc.
- [ ] Overlap with watchdog: digest watches the world, watchdog watches your repos

**Phase 5: Structured output + integrations**

- [x] MCP server mode: `digest serve` with 4 tools (generate, list_platforms, expand_query, structured_view)
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

- [ ] Study AARTS hook point model as design checklist for our agents
  - digest: PreMCPConnect (external data sources), URL reputation
  - recall: PreMemoryRead/Write (knowledge base integrity)
  - autoresearch: PreToolUse/shell (training commands), package supply chain
- [ ] Evaluate Sage ADR engine (`/plugin install sage@sage`) for Claude Code runtime protection
- [ ] Evaluate Skill IDs ([github.com/gendigitalinc/skill-id-standard](https://github.com/gendigitalinc/skill-id-standard)) for skill integrity verification between chezmoi apply runs

**Note:** AARTS is v0.1 draft, Sage is v0.4.3, Skill ID signing is a proposal. Early but worth tracking.

### Agent <-> skill integration

Skills that invoke or surface agent capabilities inside Claude Code sessions:

- [x] All 7 agents expose MCP servers via `<agent> serve` (stdio transport, FastMCP)
- [x] 5 new agent skill stubs (autoresearch, watchdog, prepper, sentinel, patchbot)
- [x] Updated digest skill with MCP config section
- [x] recall already had MCP server + skill docs
- [x] `prepper` SessionStart hook (scripts/hooks/prepper-session-start.sh + settings.json docs)
- [ ] Design proactive triggers: sentinel alerts, watchdog degradation -> session notification

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
- [ ] Track Sage MCP interception support

---

**Tech defaults:** Python (typer CLI, httpx, pydantic, sqlite3). MCP via FastMCP. Blockscout MCP for on-chain data. Deploy long-running agents to mini-axol (ansible roles ready).
