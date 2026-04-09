# TODO

## Agents

### digest (priority: high)

Multi-platform activity digest. Our version of [last30days-skill](https://github.com/mvanhorn/last30days-skill).

**Core idea:** Topic in -> synthesized brief out, weighted by credibility signals. Differential by default -- highlights what changed, not just what exists.

#### Phase 1: MVP (pull mode)

- [ ] Define platform targets: Reddit, HN, GitHub, X, YouTube (start with API-only sources)
- [ ] Design query expansion -- resolve topic to handles/subreddits/repos
- [ ] Build platform adapters (one module per source, common interface)
  - [ ] Reddit (API, oauth)
  - [ ] Hacker News (Algolia API, no auth)
  - [ ] GitHub (gh CLI or REST API)
  - [ ] X (vendored client or nitter scrape)
  - [ ] YouTube (yt-dlp for transcripts)
- [ ] Ranking algorithm: weight by engagement (upvotes, stars, views) not recency alone
- [ ] Cross-platform deduplication (same story on HN + Reddit)
- [ ] Claude synthesis step: raw data -> narrative with citations
- [ ] CLI entry point: `digest <topic> [--days 30] [--platforms reddit,hn]`
- [ ] Output formats: markdown, terminal

#### Phase 2: Web3-native sources

- [ ] Farcaster (Neynar API or hub direct)
- [ ] ethresear.ch (forum scrape or RSS)
- [ ] Snapshot/Tally governance proposals for watched DAOs
- [ ] Blockscout MCP -- on-chain activity for watched addresses (already in our stack)
- [ ] Prediction markets: Polymarket, Kalshi odds as credibility signal
- [ ] Package registries: hex.pm, crates.io, npm new releases for watched deps

#### Phase 3: Differential digests + feed memory

- [ ] Feed memory (sqlite): store past digests, track narrative arcs over time
- [ ] Differential mode: "new since last digest" vs "ongoing, declining" vs "new and accelerating"
- [ ] Source credibility scoring: track which sources were later proven wrong, downweight hype over time
- [ ] Credibility layering: prediction market odds > engagement metrics > raw volume

#### Phase 4: Proactive mode

- [ ] Watch mode: define topics of interest, run on schedule (cron/launchd)
- [ ] Alert thresholds: push notification when topic crosses engagement/credibility threshold
- [ ] Triggers: new governance proposal on watched contract, spike in discussion of a dependency, etc.
- [ ] Overlap with watchdog: digest watches the world, watchdog watches your repos

#### Phase 5: Structured output + integrations

- [ ] MCP server mode: run as MCP server so Claude Code sessions can query inline
- [ ] Structured output: controversy map, timeline view, sentiment shifts, emerging vs declining tags
- [ ] prepper integration: feed "relevant industry context" into pre-session briefings
- [ ] recall integration: store past digests for trend queries ("how has sentiment on X changed?")
- [ ] sentinel integration: on-chain events flow into web3 digest context

**Tech:** Python (typer CLI, httpx for APIs, pydantic models, sqlite3 for feed memory). MCP server via FastMCP. Blockscout MCP for on-chain data.

---

### recall (priority: medium)

Knowledge capture and retrieval. Our version of [paperclip](https://github.com/paperclipai/paperclip).

**Core idea:** Lightweight knowledge graph that captures insights from work sessions and makes them queryable.

- [ ] Define knowledge schema (what gets captured: decisions, patterns, gotchas, links)
- [ ] Storage backend: local sqlite with FTS5 for search
- [ ] Capture interface: CLI `recall add "insight"` or hook into Claude Code post-session
- [ ] Query interface: `recall search "topic"` with relevance ranking
- [ ] Auto-extraction: parse Claude Code conversation logs for key decisions
- [ ] Tag/categorize by project, topic, date
- [ ] Integration: Claude Code skill that queries recall DB for relevant context
- [ ] Prune/decay: surface stale entries for review

**Tech:** Python (typer, sqlite3, pydantic). Possibly a Claude Code hook for auto-capture.

**Key difference from paperclip:** We don't need the full org-chart/multi-agent orchestration. We want the knowledge capture loop -- watch sessions, extract insights, make them findable.

---

### autoresearch (priority: medium, deployment: mini-axol)

Autonomous ML experiment runner. Our version of [karpathy/autoresearch](https://github.com/karpathy/autoresearch).

**Core idea:** Define research objective in markdown, agent modifies code, trains, evaluates, iterates.

- [ ] Define experiment harness: fixed `prepare.py` + mutable `train.py` pattern
- [ ] Single optimization metric per experiment (validation loss, accuracy, etc.)
- [ ] Fixed time budget per run (5 min like autoresearch, tunable)
- [ ] Experiment tracker: log each run's config, metric, diff
- [ ] Agent prompt design: objective + current best + code -> proposed change
- [ ] Safety: sandbox execution, resource limits, no network during training
- [ ] Results dashboard: compare runs, show progression
- [ ] mini-axol deployment: systemd service or cron, overnight batch mode

**Tech:** Python + PyTorch. Claude API for the agent loop. Runs on mini-axol (NVIDIA GPU).

**Key insight from karpathy:** Keep scope minimal. One mutable file, one metric, fixed time budget. Complexity kills autonomous experimentation.

**Beyond ML:** The pattern (objective + mutable code + fixed budget + iteration) generalizes to: Noir circuit constraint minimization, Solidity gas optimization, compiler pass tuning. Consider making the harness domain-agnostic.

---

### watchdog (priority: low)

Continuous repo health monitor. Scans repos on a cron for stale PRs, failing CI, dependency vulns, unfixed security advisories, TODOs referencing closed issues.

- [ ] Multi-repo config: list of repos to watch
- [ ] Health checks: open PRs age, CI status, lockfile audit (npm/pip/cargo/mix/go)
- [ ] TODO scanner: find TODOs referencing closed issues or merged PRs
- [ ] Security advisory check per ecosystem (gh api, cargo-audit, mix_audit, pip-audit)
- [ ] Weekly digest output (markdown, could feed into digest agent)
- [ ] Cron deployment (mini-axol or local launchd)

**Tech:** Python (typer, gh CLI, language-specific lockfile parsers). Mostly glue.

---

### sentinel (priority: low)

On-chain contract monitor. Watches deployed contracts via Blockscout MCP for anomalous transactions, large transfers, governance proposals, known attack patterns.

- [ ] Contract watchlist config (address, chain, alert thresholds)
- [ ] Blockscout MCP integration for transaction monitoring
- [ ] Alert rules: large transfers, unusual function calls, ownership changes
- [ ] Known attack pattern matching (from solidity-audit vulnerability taxonomy)
- [ ] Notification: terminal, webhook, or email
- [ ] Continuous mode: poll interval or event-driven

**Tech:** Python (httpx, pydantic). Blockscout MCP for data. Runs on mini-axol.

---

### patchbot (priority: low)

Automated dependency updater across polyglot repos. Like Dependabot/Renovate but aware of the full stack.

- [ ] Lockfile parsing: mix.lock, Cargo.lock, package-lock.json, go.sum, requirements.txt
- [ ] Version bump detection per ecosystem
- [ ] Run test suite before opening PR (language-specific test commands)
- [ ] Batch related updates (e.g. all Elixir deps in one PR)
- [ ] Cross-repo awareness: same dep bumped across multiple repos
- [ ] PR creation via gh CLI with changelog summary

**Tech:** Python (typer, gh CLI). Wraps existing tools (mix deps.update, cargo update, npm update, go get -u).

**Differentiator from Dependabot/Renovate:** Polyglot-aware batching, runs your actual test suite, understands cross-repo dependencies.

---

### prepper (priority: low)

Pre-session context builder. Generates a briefing before starting work on a project.

- [ ] Git activity: recent commits, active branches, uncommitted changes
- [ ] GitHub state: open PRs, assigned issues, failing checks
- [ ] Dependency status: outdated packages, known vulns
- [ ] Recall integration: surface relevant knowledge entries for the project
- [ ] CI status: last run result, flaky test history
- [ ] Output: markdown briefing injected into Claude Code session context
- [ ] Hook: Claude Code SessionStart or manual `/prepper` invocation

**Tech:** Python (typer, gh CLI, sqlite3 for recall DB). Could also be a Claude Code hook.

**Key insight:** recall captures *after* sessions, prepper prepares *before*. Together they close the knowledge loop.

---

## Agent <-> skill integration

Skills that invoke or surface agent capabilities inside Claude Code sessions:

- [ ] `/digest` slash command skill -- invoke digest agent from within Claude Code
- [ ] `recall` context skill -- auto-inject relevant knowledge from recall DB into session context (Claude Code hook on SessionStart or similar)
- [ ] `autoresearch` status skill -- check experiment progress, surface latest results
- [ ] `watchdog` digest skill -- surface weekly health report in session
- [ ] `sentinel` alert skill -- check recent on-chain alerts
- [ ] `prepper` hook -- auto-inject briefing on SessionStart
- [ ] Design the boundary: agents run standalone, skills are the Claude Code interface to them

---

## Skills: cleanup and improvements

### Structural improvements (apply to all skills)

Lessons from [mattpocock/skills](https://github.com/mattpocock/skills) and [slavingia/skills](https://github.com/slavingia/skills):

- [x] Add "What You Get" sections to every SKILL.md (all 9 done)
- [x] Add anti-patterns to design-ux (Common Pitfalls table)
- [x] Promote top pitfalls in claude-api (quick-reference table near top)
- [ ] Keep SKILL.md under 100 lines, split depth into companion files (claude-api is ~280 lines)
- [ ] Add workflow/procedure skills alongside reference skills
- [ ] Consider `.claude-plugin/` marketplace format for distribution

### Existing skill audit

- [x] Run `./scripts/skills-lint.sh` -- all checks passed (0 errors, 0 warnings)
- [ ] Audit naming for consistency across all 9 skills
- [ ] Ensure all sub-files have complete frontmatter (impact, impactDescription, tags)
- [ ] Review skill cross-references (See also sections)
- [ ] Split claude-api SKILL.md (~280 lines) -- move model table, thinking/effort, caching to companion files

### Testing strategy

- [ ] Define how to test skills beyond linting (trigger accuracy, output quality)
- [ ] Consider snapshot testing: known input -> expected skill activation
- [ ] Evaluate snyk/agent-scan as a safety gate (complements lint)

### Extraction priority order

When extracting from other repos, do these first (highest impact, least effort):

1. `grill-me` (tiny, immediately useful, no adaptation needed)
2. `git-guardrails-claude-code` (practical safety, executable)
3. `tdd` (merged mattpocock + alirezarezvani, adapt for polyglot)
4. `pr-review-expert` + `code-reviewer` (merge into `code-review`)
5. `env-secrets-manager` (leak detection, directly useful)
6. `mcp-server-builder` (OpenAPI -> MCP, relevant to our MCP setup)
7. `prd-to-plan` + `prd-to-issues` (planning pipeline)
8. Everything else

---

## Skills: extraction from other repos

### From [mattpocock/skills](https://github.com/mattpocock/skills) -- process discipline

These are workflow skills (procedures with user checkpoints), not reference docs.

**Tier 1: Extract and adapt**

- [ ] `tdd` -- TDD workflow + companion files (mocking, refactoring, deep-modules, interface-design). Richer than alirezarezvani's version. Anti-horizontal-slice philosophy. Adapt for our polyglot stack (Elixir ExUnit, Go table-driven, Rust, Python pytest).
- [ ] `prd-to-plan` -- PRD -> phased "tracer bullet" vertical slices. Each phase = narrow complete path through all layers.
- [ ] `prd-to-issues` -- PRD -> GitHub issues with HITL/AFK distinction (human-in-the-loop vs autonomous). Issues in dependency order.
- [ ] `design-an-interface` -- Spawns 3+ parallel sub-agents with different constraints ("Design It Twice" from Ousterhout). Deep modules principle.
- [ ] `grill-me` -- 635-byte interview skill. One question at a time, offers recommended answers. Tiny but powerful.
- [ ] `git-guardrails-claude-code` -- PreToolUse hooks blocking dangerous git ops. Only skill with executable code.

**Tier 2: Consider**

- [ ] `triage-issue` -- Bug investigation -> GitHub issue with TDD fix plan. Describes behaviors/contracts, not file paths.
- [ ] `ubiquitous-language` -- DDD glossary extraction from conversations.
- [ ] `improve-codebase-architecture` -- Identifies shallow modules. Dependency classification (in-process, local-sub, remote-owned, true-external).
- [ ] `qa` -- Interactive QA with background explorer agent running in parallel.

### From [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) -- tooling automation

233 skills, most are business/marketing fluff. Engineering POWERFUL tier has real value.

**Tier 1: Extract (high value, no overlap)**

- [ ] `pr-review-expert` -- Blast radius analysis, security scan, 30+ item checklist. Polyglot.
- [ ] `dependency-auditor` -- Multi-language (JS, Python, Go, Rust, Ruby, Java) vuln scanning + license compliance.
- [ ] `ci-cd-pipeline-builder` -- Stack detection -> GitHub Actions/GitLab CI generation.
- [ ] `env-secrets-manager` -- Leak detection, rotation workflows, pre-commit hooks.
- [ ] `tech-debt-tracker` -- Automated debt scanning, cost-of-delay prioritization, trend dashboards.
- [ ] `release-manager` -- Changelog gen, semver bumping, readiness checks.
- [ ] `observability-designer` -- SLO/SLI design, alert optimization, dashboard generation.
- [ ] `mcp-server-builder` -- OpenAPI -> MCP server scaffolding. Directly useful for our MCP setup.
- [ ] `agent-designer` -- Multi-agent orchestration patterns, tool schemas.

**Tier 2: Adapt (useful, needs rework)**

- [ ] `tdd-guide` -- TDD workflows for Go/Pytest/Jest, mutation testing. May merge with mattpocock's richer version.
- [ ] `code-reviewer` -- SOLID violation detection, quality scoring. May merge with `pr-review-expert`.
- [ ] `focused-fix` -- Structured 5-phase bug fix methodology with root cause verification.
- [ ] `senior-architect` -- ADR workflows, dependency analysis, diagram generation.
- [ ] `changelog-generator` -- Conventional commit parsing. May merge with `release-manager`.
- [ ] `git-worktree-manager` -- Parallel dev with port isolation. Useful for multi-agent workflows.
- [ ] `database-designer` -- Schema analysis, ERD generation, index optimization.
- [ ] `performance-profiler` -- Node/Python/Go profiling. Missing Elixir/Rust but adaptable.
- [ ] `codebase-onboarding` -- Auto-generate onboarding docs from codebase analysis.
- [ ] `adversarial-reviewer` -- Devil's advocate review that challenges assumptions.
- [ ] `self-improving-agent` -- Auto-memory curation, pattern promotion.
- [ ] `rag-architect` -- RAG pipeline design for AI/LLM applications.
- [ ] `llm-cost-optimizer` -- LLM API cost optimization strategies.

### Merge plan (dedup across sources)

Some candidates overlap -- merge into single skills rather than extracting both:

- **tdd**: mattpocock (workflow + companion files) + alirezarezvani `tdd-guide` (mutation testing, Go/Pytest) -> single `tdd` skill adapted for our polyglot stack
- **pr-review**: alirezarezvani `pr-review-expert` (blast radius, 30-item checklist) + `code-reviewer` (SOLID detection) -> single `code-review` skill
- **release**: alirezarezvani `release-manager` + `changelog-generator` -> single `release` skill
- **architecture**: alirezarezvani `senior-architect` (ADRs) + mattpocock `improve-codebase-architecture` (deep modules) -> single `architect` skill

### From [slavingia/skills](https://github.com/slavingia/skills) -- design patterns only

Not extracting skills (business-focused, not relevant). Adopting these patterns to existing + new skills:

- [ ] **Output sections** -- every skill specifies what artifact the user gets
- [ ] **Anti-patterns as first-class content** -- "WRONG" examples alongside correct
- [ ] **argument-hint frontmatter** -- for advisory/meta skills that take freeform input
- [ ] **Plugin marketplace format** -- `.claude-plugin/` for distribution

---

## Distribution

- [ ] Add `.claude-plugin/marketplace.json` + `plugin.json` for Claude Code plugin marketplace
- [ ] Keep chezmoi `.chezmoiexternal.toml` method as primary install
- [ ] Support `npx skills@latest add` method
- [ ] Document both installation paths in README

---

## Agent security

### [snyk/agent-scan](https://github.com/snyk/agent-scan) -- integration

Security scanner for MCP servers, skills, and agent harnesses. Catches prompt injection, tool shadowing, malicious code, credential leaks, toxic flows.

- [ ] Run `uvx snyk-agent-scan@latest --skills ./skills/` against our skills
- [ ] Add to CI: `uvx snyk-agent-scan@latest --ci --json --skills`
- [ ] Evaluate `guard install claude` for real-time PreToolUse hooks
- [ ] Consider MCP server mode for agent self-scanning (digest, recall, autoresearch)

### [Gen Digital Agent Trust Hub](https://ai.gendigital.com/agent-trust-hub) -- standards adoption

**AARTS** (AI Agent Runtime Safety Standard) -- 19 hook points for runtime security. [github.com/gendigitalinc/aarts](https://github.com/gendigitalinc/aarts)

- [ ] Study AARTS hook point model as design checklist for our agents
  - digest: PreMCPConnect (external data sources), URL reputation
  - recall: PreMemoryRead/Write (knowledge base integrity)
  - autoresearch: PreToolUse/shell (training commands), package supply chain
- [ ] Evaluate Sage ADR engine (`/plugin install sage@sage`) for Claude Code runtime protection
- [ ] Evaluate Skill IDs ([github.com/gendigitalinc/skill-id-standard](https://github.com/gendigitalinc/skill-id-standard)) for skill integrity verification between chezmoi apply runs

**Note:** AARTS is v0.1 draft, Sage is v0.4.3, Skill ID signing is a proposal. Early but worth tracking.

---

## Research backlog

- [ ] Review [claude-skills](https://github.com/alirezarezvani/claude-skills) marketing/PM skills for any hidden gems (droo manual pass)
- [ ] Watch for new skills repos in the Claude Code ecosystem
- [ ] Evaluate [obra/superpowers-marketplace](https://github.com/obra/superpowers-marketplace) for overlap with planned workflow skills
- [ ] Track AARTS spec evolution (currently v0.1)
- [ ] Track Sage MCP interception support (not yet implemented, relevant for our MCP-heavy setup)
