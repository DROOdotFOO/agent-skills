---
name: mcp-server-builder
description: >
  Scaffold MCP servers from OpenAPI specs. TRIGGER when: user asks to build an
  MCP server, convert an OpenAPI/Swagger spec to MCP tools, generate MCP tool
  definitions, or scaffold a FastMCP/TypeScript MCP project. DO NOT TRIGGER
  when: user is configuring an existing MCP server, writing MCP clients, or
  working with Claude API directly (use claude-api skill).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: mcp, openapi, fastmcp, scaffolding, server, tools, model-context-protocol
---

# MCP Server Builder

Generate Model Context Protocol servers from OpenAPI specifications. Supports
Python (FastMCP) and TypeScript targets.

## What You Get

- Working MCP server directory scaffolded from an OpenAPI spec
- Typed tool definitions, auth wrappers, confirmation gates, and test stubs

## Workflow

1. **Parse** -- Read the OpenAPI spec (JSON or YAML), extract paths, operations,
   schemas, and auth requirements.
2. **Generate** -- Map each operation to an MCP tool definition with typed input
   schemas. Apply naming conventions (verb_noun, snake_case).
3. **Secure** -- Add auth wrappers, host allowlists, confirmation gates for
   destructive operations, and structured error payloads.
4. **Validate** -- Run the manifest through lint checks: duplicate names, missing
   descriptions, invalid schemas, naming hygiene.
5. **Test** -- Unit tests for schema transforms, contract tests for manifest
   snapshots, integration tests against a staging API.

## Quality Gates (before publishing)

- [ ] Every tool has a non-empty description
- [ ] No duplicate tool names
- [ ] All destructive operations require confirmation input
- [ ] Secrets sourced from env vars only (none in schemas or defaults)
- [ ] Host allowlist is explicit (no wildcards unless justified)
- [ ] Manifest passes strict validation (`validation.md`)
- [ ] Unit + contract tests pass
- [ ] Integration test against at least one live endpoint

## Top Pitfalls

| Mistake | Fix |
| --- | --- |
| Leaking API keys in tool schemas | Use env vars; never put secrets in `inputSchema` defaults |
| Generic tool names (`get_data`) | Use API-specific prefixes (`github_list_repos`) |
| Missing error structure | Return `{error: string, code: number}`, not raw strings |
| Huge parameter objects | Flatten or split; MCP tools work best with focused inputs |
| No confirmation on DELETE | Add `confirm: true` input for destructive operations |

## Reading Guide

| Topic | File |
| --- | --- |
| OpenAPI-to-MCP mapping, scaffold templates | `scaffolding.md` |
| Auth patterns, safety, error design | `auth-and-safety.md` |
| Manifest validation and CI checks | `validation.md` |
| Testing strategy (unit/contract/integration) | `testing.md` |
