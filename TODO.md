# TODO

## Open

### Skills

- [ ] **incident-response** -- on-call playbooks, severity classification, runbook creation, blameless postmortem/RCA. Closes gap between observability-designer and focused-fix
- [ ] **elixir-otp** -- OTP architecture beyond raxol: supervision trees, gen_server design, clustering, hot code reloading, Erlang observer
- [ ] **zk-optimization** -- ZK circuit performance engineering: constraint counting, recursion patterns, proving system trade-offs (Plonk vs Groth16)
- [ ] **api-contract** -- REST/GraphQL/gRPC spec-first design, consumer contract testing, schema evolution, breaking change detection
- [ ] **container-strategy** -- Dockerfile best practices, multi-stage builds, image scanning, deployment patterns (blue-green, canary)

### CI/CD

- [ ] **Release automation** -- version bumping, changelog (all agents frozen at 0.1.0, deferred: no consumers)
- [ ] **Snyk agent-scan** gate (deferred: server returning 503)

### Agent security

- [ ] Run `uvx snyk-agent-scan@latest --skills ./skills/` (blocked: snyk server 503)
- [ ] Add snyk to CI: `uvx snyk-agent-scan@latest --ci --json --skills`
- [ ] Evaluate `guard install claude` for real-time PreToolUse hooks
- [ ] Evaluate Skill IDs ([skill-id-standard](https://github.com/gendigitalinc/skill-id-standard)) for integrity verification
- [ ] Track AARTS spec evolution (currently v0.1)
- [ ] Track Sage MCP interception support (not in v0.8.0, needed for our 8 MCP agents)

### Digest adapters

Expand beyond tech/crypto. Full API specs in `agents/digest/SPECS.md`.

**Tier 1** (clean APIs, implement first):

- [ ] Semantic Scholar -- JSON, citationCount/velocity/TLDR, key optional
- [ ] PubMed -- JSON+XML two-step, iCite enrichment, key optional
- [ ] Federal Register -- JSON, keyless, comment_count + significant flag
- [ ] Shodan enhancements -- InternetDB fallback, facets endpoint, exploits API

**Tier 2** (moderate complexity):

- [ ] arXiv -- Atom XML, no engagement (composite with S2), 1 req/3s
- [ ] OpenAlex -- JSON, 470M+ works, fwci, email for polite pool
- [ ] CourtListener -- JSON, citeCount, free token required
- [ ] ClinicalTrials.gov -- JSON, enrollment + phase, keyless
- [ ] Congress.gov -- JSON, cosponsor count needs 2nd call, free key

**Tier 3-4** (niche): Crossref, regulations.gov, openFDA, bioRxiv, WHO DON, CDC MMWR, EUR-Lex, UK Legislation

**Shared infra**: XML parser (arXiv/PubMed/UK Legislation), ExpandedQuery extensions, credibility + ranking updates

### Research backlog

- [ ] Review alirezarezvani marketing/PM skills for hidden gems
- [ ] Watch for new skills repos in Claude Code ecosystem

---

## Completed

### 2026-04-18 -- Skill audit + consolidation + expansion

52 skills, 8 agents + shared, 771 tests, 0 lint errors.

- Researched [taste-skill](https://github.com/Leonxlnx/taste-skill): extracted persona priming pattern (5 skills + skill-creator template)
- Researched [superpowers-marketplace](https://github.com/obra/superpowers-marketplace): extracted verification-before-completion (cross-cutting in focused-fix, qa, release) + receiving-code-review (sub-file in code-review)
- Consolidated 53 -> 50: merged prd-to-plan + prd-to-issues + grill-me into prd-to-plan v2; merged triage-issue + qa into qa v2
- Expanded 50 -> 52: new property-testing (4 files, property taxonomy + generators + shrinking) and refactoring-strategy (4 files, characterization tests + patterns + large-scale strategies)
- Updated all metadata (CLAUDE.md, plugin.json, marketplace.json, trigger tests 37->41)

### 2026-04-18 -- Framework improvements

- Shared abstractions: hooks.py, models.py, config.py extracted to agents/shared/ (saved ~200 LOC)
- CI: GitHub Actions with pytest + ruff + skills-lint, Python 3.10/3.12 matrix
- CLI integration tests: 30 tests across all 8 agents via CliRunner
- Skill quality: "What You Get" enforced (52/52), .env.example, mcp.example.json

### 2026-04-16 -- Structural patterns

- Skill splits (8 skills under 100 lines), output sections (15 skills), anti-pattern examples (5 skills), argument-hint (9 skills)

### 2026-04-12 -- Scribe agent + AARTS hooks + proactive triggers

- Scribe agent: session insight extractor, 114 tests
- AARTS Phase 1+2: PreToolUse, PreMemoryWrite, PostToolUse, PreSubAgentSpawn hooks across 5 agents (136 hook tests)
- Proactive triggers: sentinel/watchdog/digest -> prepper watch -> macOS notifications
- Digest proactive mode: watch, alerts, thresholds, triggers
- Latent Briefing integration: recall relevance floors, prepper token budgets

### 2026-04-11 -- Integration + agents

- All 8 agents with MCP servers (31 tools total)
- Digest adapters: HN, GitHub, Reddit, YouTube, ethresear.ch, Snapshot, Polymarket, packages, CoinGecko, Blockscout, Shodan
- Differential digests, source credibility scoring, structured output views
- Recall: SQLite FTS5, auto-extraction, MAD-normalized relevance
- 5 advanced agents: autoresearch, watchdog, prepper, sentinel, patchbot
- 40+ skills extracted across 6 phases

### 2026-04-10 -- Initial build

- Digest MVP, 3 initial skill extractions, claude-api split
