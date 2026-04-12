# AARTS Hook Point Mapping for agent-skills

Handover document for implementing AARTS-aligned safety hooks across our 7 agents.

## What is AARTS

AARTS v0.1 (Gen Digital, 2026-02-24) defines 20 hook points across 8 categories for AI agent runtime security. It's a vendor-neutral interface: hosts fire events, security engines return verdicts (allow/deny/ask). Spec: https://github.com/gendigitalinc/aarts

Three conformance levels:
- **Level 1 (Basic)**: SessionStart + PreToolUse only
- **Level 2 (Standard)**: Adds plugin/skill loading, prompt integrity, PostToolUse
- **Level 3 (Comprehensive)**: All 20 hooks including sub-agent, memory, compaction

## Hook Points That Matter for Our Agents

### Critical (implement first)

| Hook | Our agents | What to guard | Threat |
|------|-----------|---------------|--------|
| **PreToolUse** | autoresearch, patchbot | Shell commands (experiment runs, dep updates), package installs | T003 (shell exfil), T005 (supply chain), T008 (excessive agency) |
| **PreMemoryWrite** | recall | Entries being persisted to FTS5 store -- scan for instruction-like patterns, credential strings | T012 (memory poisoning) |
| **PreMemoryRead** | recall, prepper | Recall entries loaded into briefings/synthesis -- flag entries from untrusted sources | T012 |
| **PreMCPConnect** | all 7 (they ARE MCP servers) | Validate transport, declared tools. Our agents are stdio-only which is safer than HTTP | T007 (malicious MCP) |
| **PostToolUse** | digest, sentinel | Adapter responses (HN/GitHub/Blockscout API) could contain prompt injection in titles/bodies | T001 (injection via tool output) |

### Important (Level 2)

| Hook | Our agents | What to guard | Threat |
|------|-----------|---------------|--------|
| **PreSubAgentSpawn** | autoresearch | Experiment runner spawns shell -- enforce permitted_tools, resource limits | T011 (privilege escalation), T010 (resource) |
| **PreCompact** | prepper | Briefing context compaction could lose security signals or user instructions | Compaction integrity |
| **PostLLMResponse** | digest (synthesis) | Claude synthesis output could be influenced by injected item titles | T001 |
| **PreSkillLoad** | all skills (47) | Skill files could contain hidden instructions; AARTS supports `strip_hooks` directive | T006 (malicious skill) |

### Nice to have (Level 3)

| Hook | Our agents | What to guard |
|------|-----------|---------------|
| **PreOutputDeliver** | digest, recall | Prevent credential leakage in synthesis output |
| **SessionStart/End** | prepper (SessionStart hook already exists) | Audit trail |
| **PostAskResolution** | all | Feed user decisions back to tune allowlists |

## Per-Agent Mapping

### digest
- **PostToolUse**: Sanitize adapter responses. Item titles from HN/Reddit/GitHub could contain injection attempts. The `raw` dict passes through to synthesis.
- **PostLLMResponse**: Synthesis output is user-facing narrative built from potentially hostile input.
- **PreMCPConnect**: 9 external data sources (APIs), all unauthenticated. Validate URLs against known endpoints.

### recall
- **PreMemoryWrite** (highest priority): `recall add` and `recall extract` persist to SQLite FTS5. Scan content for `<system>`, `<instructions>`, credential patterns before INSERT.
- **PreMemoryRead**: `recall search` results flow into digest synthesis and prepper briefings. Flag entries written by automated extraction vs. manual add.

### autoresearch
- **PreToolUse**: Experiment `verify` command is arbitrary shell. Enforce allowlist (e.g., only `cargo test`, `python -m pytest`, `nargo test`). Block network access during runs.
- **PreSubAgentSpawn**: Each experiment iteration is effectively a sub-agent. Enforce `permitted_tools` = [file_write to mutable files only, shell for verify/guard commands only].

### sentinel
- **PostToolUse**: Blockscout API responses parsed into Transaction objects. Validate response structure before rule evaluation.
- **PreMCPConnect**: Connects to 11 chain-specific Blockscout instances. Validate URLs match `BLOCKSCOUT_URLS` dict.

### watchdog
- **PostToolUse**: `gh` CLI output parsed for health checks. GitHub API responses could be tampered.
- **PreToolUse**: `npm audit`, `cargo audit`, `pip audit` -- these shell out to package managers.

### prepper
- **PreMemoryRead**: Loads recall entries, sentinel alerts (JSONL), digest alerts (JSONL), digest history (SQLite). All are local files but could be poisoned.
- **PreCompact**: Briefing token budget compaction (already implemented) should preserve HIGH-priority sections. AARTS formalizes this.

### patchbot
- **PreToolUse** (highest priority): Runs `mix hex.outdated`, `cargo update`, `npm update`, `go get -u`, `pip install --upgrade` -- all modify dependencies. T005 (supply chain) is the primary threat.
- Shell commands should be validated against allowlist of known update commands.

## Implementation Strategy

**Phase 1 (Level 1 -- quick wins)**:
1. Add a `hooks.py` module to each agent with a `HookResult` model (verdict: allow/deny/ask, reason: str)
2. Implement `pre_tool_use(tool_name, args)` for autoresearch and patchbot (shell command allowlists)
3. Implement `pre_memory_write(content)` for recall (pattern scanning for injection/credentials)

**Phase 2 (Level 2)**:
4. Add `post_tool_use(tool_name, result)` for digest adapters (sanitize titles/bodies)
5. Add `pre_sub_agent_spawn(config)` for autoresearch (permitted_tools enforcement)
6. Add `pre_memory_read(entries)` for prepper (source provenance flagging)

**Phase 3 (Level 3)**:
7. PostLLMResponse scanning for digest synthesis
8. PreOutputDeliver for credential leak detection
9. SessionStart/End audit logging

**Key design decisions for next agent**:
- Hooks should be opt-in per agent, not a shared framework (agents are standalone)
- Each agent's `hooks.py` returns `HookResult`; the CLI/MCP layer enforces verdicts
- Start with static allowlists, not ML-based detection (YAGNI)
- Log all deny verdicts to JSONL for audit (same pattern as sentinel/digest alerts)
- No external security engine dependency yet -- implement the hook interface so one could plug in later

## Files to Read

| File | Why |
|------|-----|
| `agents/autoresearch/src/autoresearch/cli.py` | Find where verify/guard commands are shelled out |
| `agents/patchbot/src/patchbot/cli.py` | Find where update commands are shelled out |
| `agents/recall/src/recall/store.py` | `add()` method is the PreMemoryWrite insertion point |
| `agents/digest/src/digest/adapters/*.py` | Each adapter's `fetch()` return is the PostToolUse inspection point |
| `agents/prepper/src/prepper/gatherers.py` | Each gatherer's file/DB reads are PreMemoryRead points |
| `agents/sentinel/src/sentinel/monitor.py` | `_parse_transaction()` is the PostToolUse parsing point |

## Threats NOT Relevant to Us

- **T009 (system prompt leakage)**: Our agents don't have system prompts; they're tools, not chatbots.
- **T014 (persistence via file write)**: Our agents write to known locations (SQLite, JSONL). Not arbitrary file writes.
- **T004 (web exfiltration)**: Our agents make HTTP reads (API fetches), not writes. Digest adapters are GET-only.
