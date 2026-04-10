# TODO

## Session log

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
- [ ] Run snyk/agent-scan against existing skills (needs uvx/uv -- install first)

### Phase 2: Quick Skill Extractions

- [x] `grill-me` -- interview skill adapted from [mattpocock/skills](https://github.com/mattpocock/skills)
- [x] `git-guardrails` -- PreToolUse hooks + block-dangerous-git.sh from [mattpocock/skills](https://github.com/mattpocock/skills)
- [x] `env-secrets-manager` -- leak detection, rotation, pre-commit setup from [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills)

### Phase 3: Digest Agent MVP

Multi-platform activity digest. Our version of [last30days-skill](https://github.com/mvanhorn/last30days-skill).

**Core idea:** Topic in -> synthesized brief out, weighted by credibility signals. Differential by default -- highlights what changed, not just what exists.

- [x] Scaffold agent structure (agents/digest/, pyproject.toml, typer CLI)
- [ ] Platform adapters (common interface, one module per source)
  - [x] Hacker News (Algolia API, no auth) -- live tested
  - [x] GitHub (gh CLI, repos + issues) -- live tested
  - [ ] Reddit (API, oauth)
  - [ ] X (vendored client or nitter scrape)
  - [ ] YouTube (yt-dlp for transcripts)
- [x] Query expansion -- static rules in expansion.py, substring matching, platform-specific `hn_terms`, GitHub `org:`/`repo:`/`topic:` qualifiers routed to `gh` CLI flags. LLM-based expansion deferred as future extension.
- [x] Ranking algorithm: log-weighted engagement + recency decay, per-platform weights
- [x] Cross-platform deduplication (URL normalization + title similarity via SequenceMatcher)
- [x] Claude synthesis step: raw data -> narrative with citations (code done, live test blocked on API credits as of 2026-04-10 -- `--no-synthesis` flag added as workaround)
- [x] CLI entry point: `digest generate <topic> [--days 30] [--platforms hn,github]`
- [x] Output formats: markdown (file), rich/terminal

### Phase 4: Merged Skill Extractions

Bigger extractions needing adaptation/merging. Interleaved with digest polish.

- [ ] `tdd` -- merge mattpocock (workflow + companion files: mocking, refactoring, deep-modules, interface-design) + alirezarezvani `tdd-guide` (mutation testing, Go/Pytest/Jest). Anti-horizontal-slice philosophy. Adapt for polyglot stack (Elixir ExUnit, Go table-driven, Rust, Python pytest)
- [ ] `code-review` -- merge alirezarezvani `pr-review-expert` (blast radius analysis, security scan, 30+ item checklist, polyglot) + `code-reviewer` (SOLID violation detection, quality scoring)
- [ ] `mcp-server-builder` -- OpenAPI -> MCP server scaffolding. Directly useful for our MCP-heavy setup ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
- [ ] `prd-to-plan` -- PRD -> phased "tracer bullet" vertical slices. Each phase = narrow complete path through all layers ([mattpocock/skills](https://github.com/mattpocock/skills))
- [ ] `prd-to-issues` -- PRD -> GitHub issues with HITL/AFK distinction (human-in-the-loop vs autonomous). Issues in dependency order ([mattpocock/skills](https://github.com/mattpocock/skills))

### Phase 5: Recall Agent + Digest Phase 2

Knowledge capture and retrieval. Our version of [paperclip](https://github.com/paperclipai/paperclip).

**Key difference from paperclip:** We don't need the full org-chart/multi-agent orchestration. We want the knowledge capture loop -- watch sessions, extract insights, make them findable.

**Key insight:** recall captures _after_ sessions, prepper (Phase 7) prepares _before_. Together they close the knowledge loop.

- [ ] **Recall agent MVP**
  - [ ] Define knowledge schema (what gets captured: decisions, patterns, gotchas, links)
  - [ ] Storage backend: local sqlite with FTS5 for search
  - [ ] Capture interface: CLI `recall add "insight"` or hook into Claude Code post-session
  - [ ] Query interface: `recall search "topic"` with relevance ranking
  - [ ] Auto-extraction: parse Claude Code conversation logs for key decisions
  - [ ] Tag/categorize by project, topic, date
  - [ ] Integration: Claude Code skill that queries recall DB for relevant context
  - [ ] Prune/decay: surface stale entries for review
- [ ] **Digest Phase 2: Web3-native sources**
  - [ ] Farcaster (Neynar API or hub direct)
  - [ ] ethresear.ch (forum scrape or RSS)
  - [ ] Snapshot/Tally governance proposals for watched DAOs
  - [ ] Blockscout MCP -- on-chain activity for watched addresses
  - [ ] Prediction markets: Polymarket, Kalshi odds as credibility signal
  - [ ] Package registries: hex.pm, crates.io, npm new releases for watched deps
- [ ] Wire `/digest` slash command skill
- [ ] Wire recall context skill (auto-inject relevant knowledge)

### Phase 6: Remaining Extractions + Distribution

- [ ] **Remaining skill extractions (Tier 1)**
  - [ ] `design-an-interface` -- Spawns 3+ parallel sub-agents with different constraints ("Design It Twice" from Ousterhout). Deep modules principle ([mattpocock/skills](https://github.com/mattpocock/skills))
  - [ ] `triage-issue` -- Bug investigation -> GitHub issue with TDD fix plan. Describes behaviors/contracts, not file paths ([mattpocock/skills](https://github.com/mattpocock/skills))
  - [ ] `dependency-auditor` -- Multi-language (JS, Python, Go, Rust, Ruby, Java) vuln scanning + license compliance ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `ci-cd-pipeline-builder` -- Stack detection -> GitHub Actions/GitLab CI generation ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `tech-debt-tracker` -- Automated debt scanning, cost-of-delay prioritization, trend dashboards ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `release` -- Merge `release-manager` (changelog gen, semver bumping, readiness checks) + `changelog-generator` (conventional commit parsing) ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `observability-designer` -- SLO/SLI design, alert optimization, dashboard generation ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `agent-designer` -- Multi-agent orchestration patterns, tool schemas ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
- [ ] **Tier 2 extractions** (adapt as needed)
  - [ ] `ubiquitous-language` -- DDD glossary extraction from conversations ([mattpocock/skills](https://github.com/mattpocock/skills))
  - [ ] `architect` -- Merge `improve-codebase-architecture` (identifies shallow modules, dependency classification: in-process, local-sub, remote-owned, true-external) + `senior-architect` (ADR workflows, dependency analysis, diagram generation)
  - [ ] `qa` -- Interactive QA with background explorer agent running in parallel ([mattpocock/skills](https://github.com/mattpocock/skills))
  - [ ] `focused-fix` -- Structured 5-phase bug fix methodology with root cause verification ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `git-worktree-manager` -- Parallel dev with port isolation. Useful for multi-agent workflows ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `database-designer` -- Schema analysis, ERD generation, index optimization ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `performance-profiler` -- Node/Python/Go profiling. Missing Elixir/Rust but adaptable ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `codebase-onboarding` -- Auto-generate onboarding docs from codebase analysis ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `adversarial-reviewer` -- Devil's advocate review that challenges assumptions ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `self-improving-agent` -- Auto-memory curation, pattern promotion ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `rag-architect` -- RAG pipeline design for AI/LLM applications ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
  - [ ] `llm-cost-optimizer` -- LLM API cost optimization strategies ([alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills))
- [ ] **Distribution**
  - [ ] Add `.claude-plugin/marketplace.json` + `plugin.json`
  - [ ] Keep chezmoi `.chezmoiexternal.toml` method as primary install
  - [ ] Support `npx skills@latest add` method
  - [ ] Document both installation paths in README

### Phase 7: Advanced Agents

- [ ] **Autoresearch** -- Autonomous ML experiment runner. Our version of [karpathy/autoresearch](https://github.com/karpathy/autoresearch). Deploy to mini-axol, overnight batch mode.

  **Core idea:** Define research objective in markdown, agent modifies code, trains, evaluates, iterates.

  **Key insight from karpathy:** Keep scope minimal. One mutable file, one metric, fixed time budget. Complexity kills autonomous experimentation.

  **Beyond ML:** The pattern (objective + mutable code + fixed budget + iteration) generalizes to: Noir circuit constraint minimization, Solidity gas optimization, compiler pass tuning. Consider making the harness domain-agnostic.

  - [ ] Define experiment harness: fixed `prepare.py` + mutable `train.py` pattern
  - [ ] Single optimization metric per experiment (validation loss, accuracy, etc.)
  - [ ] Fixed time budget per run (5 min like autoresearch, tunable)
  - [ ] Experiment tracker: log each run's config, metric, diff
  - [ ] Agent prompt design: objective + current best + code -> proposed change
  - [ ] Safety: sandbox execution, resource limits, no network during training
  - [ ] Results dashboard: compare runs, show progression
  - [ ] mini-axol deployment: systemd service or cron, overnight batch mode

  **Tech:** Python + PyTorch. Claude API for the agent loop. Runs on mini-axol (NVIDIA GPU).

- [ ] **Watchdog** -- Continuous repo health monitor. Scans repos on a cron for stale PRs, failing CI, dependency vulns, unfixed security advisories, TODOs referencing closed issues.
  - [ ] Multi-repo config: list of repos to watch
  - [ ] Health checks: open PRs age, CI status, lockfile audit (npm/pip/cargo/mix/go)
  - [ ] TODO scanner: find TODOs referencing closed issues or merged PRs
  - [ ] Security advisory check per ecosystem (gh api, cargo-audit, mix_audit, pip-audit)
  - [ ] Weekly digest output (markdown, could feed into digest agent)
  - [ ] Cron deployment (mini-axol or local launchd)

  **Tech:** Python (typer, gh CLI, language-specific lockfile parsers). Mostly glue.

- [ ] **Prepper** -- Pre-session context builder. Generates a briefing before starting work on a project.

  **Key insight:** recall captures _after_ sessions, prepper prepares _before_. Together they close the knowledge loop.

  - [ ] Git activity: recent commits, active branches, uncommitted changes
  - [ ] GitHub state: open PRs, assigned issues, failing checks
  - [ ] Dependency status: outdated packages, known vulns
  - [ ] Recall integration: surface relevant knowledge entries for the project
  - [ ] CI status: last run result, flaky test history
  - [ ] Output: markdown briefing injected into Claude Code session context
  - [ ] Hook: Claude Code SessionStart or manual `/prepper` invocation

  **Tech:** Python (typer, gh CLI, sqlite3 for recall DB). Could also be a Claude Code hook.

- [ ] **Sentinel** -- On-chain contract monitor. Watches deployed contracts via Blockscout MCP for anomalous transactions, large transfers, governance proposals, known attack patterns.
  - [ ] Contract watchlist config (address, chain, alert thresholds)
  - [ ] Blockscout MCP integration for transaction monitoring
  - [ ] Alert rules: large transfers, unusual function calls, ownership changes
  - [ ] Known attack pattern matching (from solidity-audit vulnerability taxonomy)
  - [ ] Notification: terminal, webhook, or email
  - [ ] Continuous mode: poll interval or event-driven

  **Tech:** Python (httpx, pydantic). Blockscout MCP for data. Runs on mini-axol.

- [ ] **Patchbot** -- Automated dependency updater across polyglot repos. Like Dependabot/Renovate but aware of the full stack.

  **Differentiator from Dependabot/Renovate:** Polyglot-aware batching, runs your actual test suite, understands cross-repo dependencies.

  - [ ] Lockfile parsing: mix.lock, Cargo.lock, package-lock.json, go.sum, requirements.txt
  - [ ] Version bump detection per ecosystem
  - [ ] Run test suite before opening PR (language-specific test commands)
  - [ ] Batch related updates (e.g. all Elixir deps in one PR)
  - [ ] Cross-repo awareness: same dep bumped across multiple repos
  - [ ] PR creation via gh CLI with changelog summary

  **Tech:** Python (typer, gh CLI). Wraps existing tools (mix deps.update, cargo update, npm update, go get -u).

---

## Deferred / Ongoing

### Digest advanced phases (after Phase 5)

**Phase 3: Differential digests + feed memory**

- [ ] Feed memory (sqlite): store past digests, track narrative arcs over time
- [ ] Differential mode: "new since last digest" vs "ongoing, declining" vs "new and accelerating"
- [ ] Source credibility scoring: track which sources were later proven wrong, downweight hype over time
- [ ] Credibility layering: prediction market odds > engagement metrics > raw volume

**Phase 4: Proactive mode**

- [ ] Watch mode: define topics of interest, run on schedule (cron/launchd)
- [ ] Alert thresholds: push notification when topic crosses engagement/credibility threshold
- [ ] Triggers: new governance proposal on watched contract, spike in discussion of a dependency, etc.
- [ ] Overlap with watchdog: digest watches the world, watchdog watches your repos

**Phase 5: Structured output + integrations**

- [ ] MCP server mode: run as MCP server so Claude Code sessions can query inline
- [ ] Structured output: controversy map, timeline view, sentiment shifts, emerging vs declining tags
- [ ] prepper integration: feed "relevant industry context" into pre-session briefings
- [ ] recall integration: store past digests for trend queries ("how has sentiment on X changed?")
- [ ] sentinel integration: on-chain events flow into web3 digest context

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

- [ ] `/digest` slash command skill -- invoke digest agent from within Claude Code
- [ ] `recall` context skill -- auto-inject relevant knowledge from recall DB into session context (Claude Code hook on SessionStart or similar)
- [ ] `autoresearch` status skill -- check experiment progress, surface latest results
- [ ] `watchdog` digest skill -- surface weekly health report in session
- [ ] `sentinel` alert skill -- check recent on-chain alerts
- [ ] `prepper` hook -- auto-inject briefing on SessionStart
- [ ] Design the boundary: agents run standalone, skills are the Claude Code interface to them

### Skills structural patterns (apply as we go)

Lessons from [mattpocock/skills](https://github.com/mattpocock/skills) and [slavingia/skills](https://github.com/slavingia/skills):

- [ ] Keep SKILL.md under 100 lines, split depth into companion files
- [ ] Add workflow/procedure skills alongside reference skills
- [ ] **Output sections** -- every skill specifies what artifact the user gets
- [ ] **Anti-patterns as first-class content** -- "WRONG" examples alongside correct
- [ ] **argument-hint frontmatter** -- for advisory/meta skills that take freeform input
- [ ] Consider `.claude-plugin/` marketplace format for distribution

### Testing strategy

- [ ] Define how to test skills beyond linting (trigger accuracy, output quality)
- [ ] Consider snapshot testing: known input -> expected skill activation
- [ ] Evaluate snyk/agent-scan as a safety gate

### Research backlog

- [ ] Review alirezarezvani marketing/PM skills for hidden gems (manual pass)
- [ ] Watch for new skills repos in Claude Code ecosystem
- [ ] Evaluate [obra/superpowers-marketplace](https://github.com/obra/superpowers-marketplace) for overlap
- [ ] Track AARTS spec evolution (currently v0.1)
- [ ] Track Sage MCP interception support

---

**Tech defaults:** Python (typer CLI, httpx, pydantic, sqlite3). MCP via FastMCP. Blockscout MCP for on-chain data. Deploy long-running agents to mini-axol (ansible roles ready).
