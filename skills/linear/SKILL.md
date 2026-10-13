---
name: linear
description: >
  Linear MCP reference for issues, projects, cycles, milestones, comments,
  documents, releases, and diffs through Linear's hosted MCP server.
  TRIGGER when: user mentions Linear, a Linear issue key like LIN-123 or ENG-42,
  asks to create/update/find Linear issues or projects, summarize a cycle, post
  standup notes to Linear, or uses linear MCP tools.
  DO NOT TRIGGER when: user asks for GitHub issues or PRs (use prd-to-plan, qa,
  or watchdog skills), or configures the raxol-symphony Linear tracker (use
  raxol-symphony skill).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: linear, mcp, issues, projects, planning
---

# Linear MCP

Linear's hosted MCP server (`https://mcp.linear.app/mcp`, Streamable HTTP,
OAuth 2.1). 68 tools on read-write, 38 on `/mcp/readonly`. Tool names are
`mcp__linear__<tool>` in hosts that namespace MCP tools.

## Strict rules

- Never invent an issue key, team, or project. Resolve names with `list_teams`,
  `list_projects`, `list_users`, `list_issue_statuses` before writing.
- `save_*` tools create when `id` is omitted and update when it is set. Never
  pass `id` on create; never omit it on update.
- Before any write that touches more than one object (bulk comments, project
  scaffolding, label replacement), show the exact plan and wait for approval.
- `labels` replaces the whole label set; use `addLabels` / `removeLabels` for
  incremental changes.
- `share_issue`, `unshare_issue`, `submit_diff_review`, `merge_diff`, and every
  `delete_*` / `retire_*` tool require an explicit user request.

## Identifiers

| Object  | Accepts                                          |
| ------- | ------------------------------------------------ |
| Issue   | `LIN-123` key or UUID                            |
| Project | `P-ENG-123`, slug, name, or UUID                 |
| Team    | key, name, or UUID                               |
| User    | UUID, name, email, or `"me"`                     |
| Cycle   | name, number, or UUID                            |
| State   | type (`triage`, `started`, ...), name, or UUID   |

Workspace: `get_workspace`. Current user's queue: `list_issues(assignee="me")`.

## Endpoint choice

| Need                         | Endpoint                               |
| ---------------------------- | -------------------------------------- |
| Create/update anything       | `https://mcp.linear.app/mcp`           |
| Reporting, summaries, triage | `https://mcp.linear.app/mcp/readonly`  |

`/mcp/readonly` is enforced server-side: write tools are absent from
`tools/list` and `tools/call` on one returns `Tool save_issue not found`, even
with a read-write token. The `/sse` endpoint is deprecated.

## Reference

| File                                     | Topic                                              |
| ---------------------------------------- | -------------------------------------------------- |
| [tools-reference.md](tools-reference.md) | All 68 tools grouped by object, RO flag, arguments |
| [usage-patterns.md](usage-patterns.md)   | Standup -> comments, plan -> project, cycle report |
| [mcp-setup.md](mcp-setup.md)             | Claude Code, Codex, Raxol setup and re-auth        |

## What You Get

- Complete, live-captured inventory of Linear MCP tools with read-only markers and key arguments.
- Identifier resolution rules and write guardrails that avoid duplicate issues and destructive label/relation edits.
- Host setup for Claude Code, Codex, and Raxol, including read-only pinning and OAuth recovery.

## See also

- `raxol-symphony` -- tracker-driven agent orchestration that reads Linear via GraphQL
- `prd-to-plan` -- PRD to phased plan; GitHub issue output
- `qa` -- bug triage and GitHub issue creation
- `prepper` -- pre-session briefings
