---
title: MCP Manifest Validation
impact: HIGH
impactDescription: Lint and validation rules for MCP server manifests before deployment
tags: mcp, validation, lint, ci, schema, naming
---

# MCP Manifest Validation

Run these checks against the generated MCP server before publishing.
In strict mode (CI), any violation is a hard failure.

## Checks

### 1. Duplicate Tool Names

Every tool name must be unique within the server. Duplicates cause silent
overwrites or runtime errors depending on the SDK.

```python
def check_duplicates(tools: list[dict]) -> list[str]:
    seen: dict[str, int] = {}
    errors: list[str] = []
    for tool in tools:
        name = tool["name"]
        seen[name] = seen.get(name, 0) + 1
    for name, count in seen.items():
        if count > 1:
            errors.append(f"Duplicate tool name: {name} (appears {count} times)")
    return errors
```

### 2. Missing Descriptions

Every tool must have a non-empty `description`. LLMs use descriptions to
decide when to invoke a tool -- missing descriptions cause poor routing.

```python
def check_descriptions(tools: list[dict]) -> list[str]:
    errors: list[str] = []
    for tool in tools:
        if not tool.get("description", "").strip():
            errors.append(f"Tool {tool['name']} has no description")
    return errors
```

### 3. Invalid Input Schemas

Tool `inputSchema` must be valid JSON Schema (draft 2020-12 or 07).
Check for:
- Properties without `type` field
- Required fields not listed in `properties`
- `enum` with zero values
- Circular `$ref` chains

```python
import jsonschema

def check_schemas(tools: list[dict]) -> list[str]:
    errors: list[str] = []
    for tool in tools:
        schema = tool.get("inputSchema", {})
        try:
            jsonschema.Draft202012Validator.check_schema(schema)
        except jsonschema.SchemaError as e:
            errors.append(f"Tool {tool['name']}: invalid schema -- {e.message}")
        # Check required fields exist in properties
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        for field in required:
            if field not in properties:
                errors.append(
                    f"Tool {tool['name']}: required field '{field}' "
                    f"not in properties"
                )
    return errors
```

### 4. Naming Hygiene

Tool names must follow conventions:

```python
import re

VALID_NAME = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")

def check_naming(tools: list[dict]) -> list[str]:
    errors: list[str] = []
    prefixes: set[str] = set()
    for tool in tools:
        name = tool["name"]
        if not VALID_NAME.match(name):
            errors.append(
                f"Tool name '{name}' must be snake_case "
                f"(lowercase letters, digits, underscores)"
            )
        parts = name.split("_")
        if len(parts) >= 2:
            prefixes.add(parts[0])
    # Warn if mixed prefixes suggest inconsistent naming
    if len(prefixes) > 3:
        errors.append(
            f"Too many verb prefixes ({len(prefixes)}): {sorted(prefixes)}. "
            f"Consider standardizing on get/list/create/update/delete."
        )
    return errors
```

### 5. Destructive Operations Without Confirmation

Tools whose names start with `delete_`, `drop_`, `purge_`, `revoke_`, or
`destroy_` must include a `confirm` boolean parameter:

```python
DESTRUCTIVE_PREFIXES = ("delete_", "drop_", "purge_", "revoke_", "destroy_")

def check_destructive_confirmation(tools: list[dict]) -> list[str]:
    errors: list[str] = []
    for tool in tools:
        name = tool["name"]
        if any(name.startswith(p) for p in DESTRUCTIVE_PREFIXES):
            props = tool.get("inputSchema", {}).get("properties", {})
            if "confirm" not in props:
                errors.append(
                    f"Destructive tool '{name}' must have a 'confirm' parameter"
                )
    return errors
```

## Running Validation

### As a script

```python
def validate_manifest(tools: list[dict], strict: bool = False) -> bool:
    """Validate all tools. Returns True if valid."""
    all_errors: list[str] = []
    all_errors.extend(check_duplicates(tools))
    all_errors.extend(check_descriptions(tools))
    all_errors.extend(check_schemas(tools))
    all_errors.extend(check_naming(tools))
    all_errors.extend(check_destructive_confirmation(tools))

    for error in all_errors:
        print(f"  [FAIL] {error}")

    if all_errors and strict:
        raise SystemExit(1)

    return len(all_errors) == 0
```

### CI Integration

Add to your CI pipeline (GitHub Actions example):

```yaml
- name: Validate MCP manifest
  run: |
    python -c "
    import json
    from validate_mcp import validate_manifest
    with open('mcp_manifest.json') as f:
        tools = json.load(f)['tools']
    validate_manifest(tools, strict=True)
    "
```

### Pre-commit hook

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: mcp-validate
      name: MCP manifest validation
      entry: python scripts/validate_mcp.py
      language: python
      files: 'mcp_manifest\.json$'
```
