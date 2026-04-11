---
title: MCP Server Testing Strategy
impact: HIGH
impactDescription: Testing layers for MCP servers -- unit, contract, integration, resilience
tags: mcp, testing, unit-tests, contract-tests, integration, resilience
---

# MCP Server Testing Strategy

Four layers of testing, from fastest to most comprehensive.

## 1. Unit Tests -- Schema Transformation

Test that OpenAPI operations produce correct MCP tool definitions.
These are pure functions, fast, no network required.

### Python (pytest)

```python
from mcp_builder import openapi_to_tool

def test_get_endpoint_produces_tool():
    operation = {
        "operationId": "getUser",
        "summary": "Get a user by ID",
        "parameters": [
            {"name": "user_id", "in": "path", "required": True,
             "schema": {"type": "string"}}
        ],
    }
    tool = openapi_to_tool("GET", "/users/{user_id}", operation)

    assert tool["name"] == "get_user"
    assert tool["description"] == "Get a user by ID"
    assert "user_id" in tool["inputSchema"]["properties"]
    assert "user_id" in tool["inputSchema"]["required"]

def test_delete_endpoint_gets_confirm_param():
    operation = {
        "operationId": "deleteUser",
        "summary": "Delete a user",
        "parameters": [
            {"name": "user_id", "in": "path", "required": True,
             "schema": {"type": "string"}}
        ],
    }
    tool = openapi_to_tool("DELETE", "/users/{user_id}", operation)

    assert tool["name"] == "delete_user"
    assert "confirm" in tool["inputSchema"]["properties"]
    assert tool["inputSchema"]["properties"]["confirm"]["type"] == "boolean"

def test_list_endpoint_uses_list_prefix():
    operation = {
        "operationId": "getUsers",
        "summary": "List all users",
        "parameters": [
            {"name": "page", "in": "query", "schema": {"type": "integer"}}
        ],
    }
    # Heuristic: GET returning array -> list_ prefix
    tool = openapi_to_tool("GET", "/users", operation, returns_array=True)

    assert tool["name"] == "list_users"
    assert "page" not in tool["inputSchema"].get("required", [])

def test_request_body_flattened():
    operation = {
        "operationId": "createUser",
        "summary": "Create a user",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                        },
                        "required": ["name", "email"],
                    }
                }
            }
        },
    }
    tool = openapi_to_tool("POST", "/users", operation)

    assert tool["name"] == "create_user"
    assert "name" in tool["inputSchema"]["properties"]
    assert "email" in tool["inputSchema"]["properties"]
```

### TypeScript (vitest)

```typescript
import { describe, it, expect } from "vitest";
import { openapiToTool } from "../src/builder.js";

describe("openapiToTool", () => {
  it("maps GET with path param to get_ tool", () => {
    const tool = openapiToTool("GET", "/users/{user_id}", {
      operationId: "getUser",
      summary: "Get a user by ID",
      parameters: [
        { name: "user_id", in: "path", required: true, schema: { type: "string" } },
      ],
    });

    expect(tool.name).toBe("get_user");
    expect(tool.inputSchema.properties).toHaveProperty("user_id");
    expect(tool.inputSchema.required).toContain("user_id");
  });

  it("adds confirm param to DELETE tools", () => {
    const tool = openapiToTool("DELETE", "/users/{user_id}", {
      operationId: "deleteUser",
      summary: "Delete a user",
      parameters: [
        { name: "user_id", in: "path", required: true, schema: { type: "string" } },
      ],
    });

    expect(tool.inputSchema.properties).toHaveProperty("confirm");
  });
});
```

## 2. Contract Tests -- Manifest Snapshots

Snapshot the generated manifest and diff against it on changes.
Catches unintentional schema drift.

```python
import json
from pathlib import Path

SNAPSHOT_PATH = Path("tests/snapshots/manifest.json")

def test_manifest_matches_snapshot(generated_manifest: dict):
    if not SNAPSHOT_PATH.exists():
        # First run: create snapshot
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(generated_manifest, indent=2))
        return

    snapshot = json.loads(SNAPSHOT_PATH.read_text())
    assert generated_manifest == snapshot, (
        "Manifest has changed. If intentional, delete the snapshot and re-run."
    )
```

### When snapshots break

- Intentional change: delete snapshot, re-run tests to regenerate
- Unintentional: investigate what changed in the OpenAPI spec or builder logic
- CI should fail on snapshot mismatch (never auto-update in CI)

## 3. Integration Tests -- Staging API

Test against a real (staging) API to verify end-to-end behavior.
These are slower and require network access.

```python
import os
import pytest

STAGING_URL = os.environ.get("STAGING_API_URL")

@pytest.mark.skipif(not STAGING_URL, reason="STAGING_API_URL not set")
class TestIntegration:
    def test_list_items_returns_data(self, mcp_client):
        result = mcp_client.call_tool("list_items", {"page": 1, "per_page": 5})
        data = result["content"][0]["text"]
        parsed = json.loads(data)
        assert isinstance(parsed, list)
        assert len(parsed) <= 5

    def test_get_nonexistent_item_returns_error(self, mcp_client):
        result = mcp_client.call_tool("get_item", {"item_id": "nonexistent-id"})
        data = json.loads(result["content"][0]["text"])
        assert data["code"] == 404

    def test_delete_without_confirm_blocked(self, mcp_client):
        result = mcp_client.call_tool(
            "delete_item", {"item_id": "test-id", "confirm": False}
        )
        data = json.loads(result["content"][0]["text"])
        assert data["code"] == 400
        assert "confirm" in data["error"].lower()
```

## 4. Resilience Tests -- Error Simulation

Verify the server handles upstream failures gracefully.
Use `respx` (Python) or `msw` (TypeScript) to simulate HTTP errors.

### Python (respx)

```python
import httpx
import respx

@respx.mock
def test_upstream_500_returns_structured_error(mcp_server):
    respx.get("https://api.example.com/items").mock(
        return_value=httpx.Response(500, json={"message": "Internal Server Error"})
    )
    result = mcp_server.call_tool("list_items", {})
    data = json.loads(result["content"][0]["text"])

    assert data["code"] == 500
    assert "error" in data
    # Must not expose raw upstream response body
    assert "Internal Server Error" not in data.get("details", {}).get("raw", "")

@respx.mock
def test_upstream_timeout_returns_error(mcp_server):
    respx.get("https://api.example.com/items").mock(
        side_effect=httpx.ReadTimeout("timeout")
    )
    result = mcp_server.call_tool("list_items", {})
    data = json.loads(result["content"][0]["text"])

    assert data["code"] >= 500
    assert "timeout" in data["error"].lower()

@respx.mock
def test_429_includes_retry_hint(mcp_server):
    respx.get("https://api.example.com/items").mock(
        return_value=httpx.Response(
            429,
            headers={"Retry-After": "30"},
            json={"message": "Rate limited"},
        )
    )
    result = mcp_server.call_tool("list_items", {})
    data = json.loads(result["content"][0]["text"])

    assert data["code"] == 429
    assert "retry" in data["error"].lower() or "details" in data
```

### TypeScript (msw)

```typescript
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

const mockServer = setupServer(
  http.get("https://api.example.com/items", () => {
    return HttpResponse.json({ message: "Server Error" }, { status: 500 });
  })
);

beforeAll(() => mockServer.listen());
afterAll(() => mockServer.close());

it("returns structured error on upstream 500", async () => {
  const result = await mcpClient.callTool("list_items", {});
  const data = JSON.parse(result.content[0].text);

  expect(data.code).toBe(500);
  expect(data).toHaveProperty("error");
});
```

## Test Organization

```
tests/
  unit/
    test_schema_transform.py    # Layer 1: pure function tests
  contract/
    test_manifest_snapshot.py   # Layer 2: snapshot diffs
    snapshots/
      manifest.json
  integration/
    test_staging_api.py         # Layer 3: live API
    conftest.py                 # MCP client fixture
  resilience/
    test_error_handling.py      # Layer 4: failure simulation
```

### CI configuration

- Unit + contract tests: run on every PR
- Integration tests: run on merge to main (requires staging credentials)
- Resilience tests: run on every PR (no network needed, uses mocks)
