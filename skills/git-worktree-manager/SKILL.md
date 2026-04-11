---
name: git-worktree-manager
description: >
  Parallel development with git worktrees and deterministic port isolation.
  TRIGGER when: user wants to work on multiple branches simultaneously, run
  parallel agent sessions, manage worktree-based dev environments, or asks
  about port conflicts between concurrent services. DO NOT TRIGGER when:
  simple branch switching (use git checkout), or single-branch development
  with no parallelism needed.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: git, worktree, parallel-dev, port-isolation, multi-agent
---

# git-worktree-manager

Parallel development using git worktrees with deterministic port allocation.
Designed for multi-agent workflows where multiple branches run services
concurrently without port collisions.

## What You Get

- Worktree lifecycle management (create, list, cleanup)
- Deterministic port allocation with collision detection
- Docker Compose patterns for per-worktree services
- Decision matrix for when worktrees add value

## Workflow

1. **Decide** -- Check the decision matrix below. Worktrees add overhead;
   use them only when parallelism is required.
2. **Create** -- `git worktree add ../project-feature feature-branch`
3. **Allocate ports** -- Use deterministic formula from port-allocation.md
4. **Run sessions** -- Each worktree gets isolated services on unique ports
5. **Cleanup** -- `git worktree remove ../project-feature` and release ports

## Decision matrix

| Situation                                  | Use worktree? | Why                                      |
| ------------------------------------------ | ------------- | ---------------------------------------- |
| Quick fix while feature branch is running  | Yes           | Keep feature services up, fix on main    |
| Multiple agents working different features | Yes           | Each agent gets isolated environment     |
| Long-running test suite on one branch      | Yes           | Continue development without waiting     |
| Simple feature branch, no running services | No            | git checkout is simpler                  |
| Reviewing a PR locally                     | Maybe         | Only if your current branch has state    |
| Shared database migrations in flight       | No            | Worktrees share .git; migrations collide |

## Rules

1. Never create worktrees inside the main working tree
2. Use sibling directories: `../project-feature`, not `./worktrees/feature`
3. Always allocate ports before starting services
4. Clean up worktrees when the branch is merged
5. Commit or stash before removing a worktree

## Reading guide

| Working on                                       | Read                                              |
| ------------------------------------------------ | ------------------------------------------------- |
| Port formula, collision checks, Docker Compose   | [port-allocation](port-allocation.md)             |
