---
name: agent-designer
description: |
  Multi-agent system design with orchestration patterns, tool schemas, and guardrails.
  TRIGGER when: user asks to design an agent system, choose agent architecture, define tool schemas, add guardrails, or evaluate agent performance; user runs /agent-design or /agent-architect.
  DO NOT TRIGGER when: using a specific agent framework (use framework docs), writing prompts for single-turn LLM calls, general API integration without agent orchestration.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: agents,multi-agent,orchestration,tool-design,guardrails,evaluation
---

# Agent Designer Skill

Design robust multi-agent systems: define agent roles, choose an architecture pattern, design tool interfaces, add safety guardrails, and evaluate performance.

## Workflow

1. **Define roles** -- Identify distinct agent responsibilities. Each agent should have a single clear purpose.
2. **Choose architecture** -- Select the orchestration pattern that fits the problem. See [architecture-patterns.md](architecture-patterns.md).
3. **Design tools** -- Define the tool schemas agents will use. See [tool-design.md](tool-design.md).
4. **Add guardrails** -- Layer in validation, human-in-the-loop gates, and failure handling. See [guardrails.md](guardrails.md).
5. **Evaluate** -- Measure task completion, quality, cost, and latency. Iterate on weak points.

## Agent Role Definition

Each agent should be specified with:

```
Agent: code-reviewer
Purpose: Review code changes for bugs, security issues, and style violations
Inputs: diff (string), file_context (string[]), review_guidelines (string)
Outputs: findings (Finding[]), verdict (PASS | FAIL), summary (string)
Tools: read_file, grep_codebase, run_linter
Constraints: read-only access, no code modification, max 5 tool calls per file
```

Keep agent scope narrow. An agent that "does everything" is just a prompt with no structure. If an agent needs more than 5-7 tools, it is probably two agents.

## Architecture Selection Guide

| Agents | Complexity | Pattern         | Example                        |
|--------|------------|-----------------|--------------------------------|
| 1      | Low        | Single Agent    | Code reviewer, summarizer      |
| 2-3    | Medium     | Pipeline        | Research -> Draft -> Edit      |
| 3-5    | Medium     | Supervisor      | Manager delegates to workers   |
| 5+     | High       | Hierarchical    | Multi-level delegation         |
| Dynamic| High       | Swarm           | Agents spawn/recruit as needed |

See [architecture-patterns.md](architecture-patterns.md) for detailed trade-offs.

## Output Format

```
System: PR Review Pipeline
Architecture: Pipeline (3 stages)
Agents: code-analyzer -> security-scanner -> summary-writer
Tools: 8 total (3 shared, 5 agent-specific)
Guardrails: input validation, output filtering, 30s timeout per agent
Estimated cost: ~$0.05 per PR (avg 500 lines)
```

## What You Get

- An agent architecture document specifying each agent's role, inputs, outputs, tools, and constraints.
- An orchestration pattern recommendation (pipeline, supervisor, hierarchical, or swarm) with rationale.
- Tool schemas, guardrail definitions, and estimated per-invocation cost for the complete system.

## Sub-files

| File                                                   | Content                                    |
|--------------------------------------------------------|--------------------------------------------|
| [architecture-patterns.md](architecture-patterns.md)   | Orchestration patterns, communication      |
| [tool-design.md](tool-design.md)                       | Schema design, error handling, idempotency |
| [guardrails.md](guardrails.md)                         | Safety, memory, failure handling, eval      |
