---
title: Architecture Patterns
impact: CRITICAL
impactDescription: Wrong architecture choice creates coordination overhead that dominates useful work
tags: agents,architecture,orchestration,multi-agent,communication
---

# Architecture Patterns

Patterns for organizing multiple agents, with trade-offs and selection criteria.

## Single Agent

One agent with access to multiple tools. No coordination overhead.

```
User -> Agent -> [Tool A, Tool B, Tool C] -> Response
```

**When to use:** Task is well-defined, tools are complementary, no parallelism needed.
**Advantages:** Simple, low latency, easy to debug.
**Disadvantages:** Breaks down with >7 tools (agent loses focus), no specialization.

## Supervisor

A manager agent delegates subtasks to specialized worker agents and synthesizes their outputs.

```
User -> Supervisor -> [Worker A, Worker B, Worker C] -> Supervisor -> Response
```

**When to use:** Subtasks are independent, workers have distinct expertise, results need synthesis.
**Advantages:** Clear ownership, workers can be developed/tested independently, parallel execution.
**Disadvantages:** Supervisor is a bottleneck, single point of failure, added latency for coordination.

**Implementation notes:**
- Supervisor decides which workers to invoke and in what order
- Workers do not communicate with each other directly
- Supervisor handles conflicts between worker outputs
- Keep worker count under 5 to avoid supervisor decision fatigue

## Swarm

Agents self-organize without a central coordinator. Each agent decides whether to handle a task or hand off to another agent.

```
User -> Agent A <-> Agent B <-> Agent C -> Response
```

**When to use:** Dynamic workloads where the number and type of agents needed is not known upfront.
**Advantages:** Flexible, resilient to individual agent failure, scales dynamically.
**Disadvantages:** Hard to debug, unpredictable execution paths, risk of infinite loops.

**Implementation notes:**
- Each agent has a handoff policy (conditions for transferring control)
- Shared context object tracks conversation state across handoffs
- Set a maximum handoff count to prevent loops
- Log every handoff with reason for post-hoc analysis

## Hierarchical

Multiple levels of delegation. Top-level agent breaks the problem down, mid-level agents manage sub-problems, leaf agents execute.

```
User -> Director -> [Manager A -> [Worker 1, Worker 2],
                     Manager B -> [Worker 3, Worker 4]]
```

**When to use:** Complex tasks with natural hierarchical decomposition (e.g., build a full application).
**Advantages:** Scales to large problems, mirrors organizational structure, separation of concerns.
**Disadvantages:** High coordination cost, deep call chains add latency, complex failure propagation.

**Implementation notes:**
- Each level should add value (decomposition, quality control, synthesis) -- do not add levels for structure alone
- Limit depth to 3 levels maximum
- Each manager handles 2-4 workers

## Pipeline

Agents execute sequentially, each transforming the output for the next stage.

```
User -> Agent A -> Agent B -> Agent C -> Response
```

**When to use:** Task has natural sequential phases (research, draft, review, publish).
**Advantages:** Simple flow, each agent has focused context, easy to test stage by stage.
**Disadvantages:** No parallelism, failure in any stage blocks the pipeline, total latency is sum of all stages.

**Implementation notes:**
- Define clear input/output contracts between stages
- Add validation between stages (reject malformed intermediate output early)
- Consider adding a feedback loop: final stage can request re-execution of earlier stages

## Communication Patterns

### Message passing

Agents exchange structured messages. Each message has a sender, recipient, type, and payload. Good for loose coupling.

### Shared state

Agents read and write to a shared data store (context object, database, file system). Good for collaborative editing. Risk: race conditions, stale reads.

### Event-driven

Agents publish events to a bus. Other agents subscribe to event types they care about. Good for extensibility. Risk: hard to trace execution flow.

## Orchestration Modes

| Mode          | Control           | Best for                              |
|---------------|-------------------|---------------------------------------|
| Centralized   | One coordinator   | Well-defined workflows, < 5 agents    |
| Decentralized | Peer-to-peer      | Dynamic workloads, autonomous agents  |
| Hybrid         | Coordinator + autonomy | Most production systems          |

Hybrid is the most common in practice: a coordinator handles the happy path, but agents have autonomy to handle edge cases and retry locally before escalating.
