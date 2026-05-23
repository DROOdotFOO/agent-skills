---
title: Variant Analysis
impact: CRITICAL
impactDescription: Finding one bug without searching for variants leaves the same class of vulnerability elsewhere in the codebase
tags: variant-analysis,trail-of-bits,pattern-search,codeql,semgrep,systematic
---

# Variant Analysis

Trail of Bits methodology: when you find a bug, systematically search for every
instance of the same pattern across the codebase. A single SQL injection means
the developer likely wrote SQL the same way everywhere.

## The 4-Step Process

### Step 1: Find

Identify the initial vulnerability. Document exactly what makes it exploitable:
- What is the source (attacker-controlled input)?
- What is the sink (dangerous operation)?
- What sanitization is missing?
- What is the data flow from source to sink?

Example finding:
```
Source: req.query.username (HTTP query parameter)
Sink: db.query(`SELECT * FROM users WHERE name = '${username}'`)
Missing: parameterized query
Flow: HTTP handler -> db.query() with string interpolation
```

### Step 2: Characterize

Generalize the vulnerability into a pattern. Strip away the specific variable names
and endpoint details. What remains is the abstract vulnerability class.

From the example above:
```
Pattern: string interpolation/concatenation into SQL query
Language: TypeScript
Signature: any call to db.query(), db.execute(), pool.query() where
           the SQL string contains template literals or concatenation
```

Key questions for characterization:
- Is this a framework-level issue or developer-level?
- Does the pattern appear in library code or application code?
- Are there wrappers or helper functions that should be enforcing safety?
- Is there a safe API that exists but was not used?

### Step 3: Search

Systematically search the entire codebase for every instance of the pattern.
Use multiple search strategies in order of increasing sophistication:

#### Strategy A: Text search (grep/ripgrep)

Fast first pass. High recall, lower precision.

```bash
# SQL injection variants
rg 'db\.(query|execute)\s*\(' --type ts -l
rg 'f".*SELECT.*{' --type py -l
rg 'fmt\.Sprintf.*SELECT' --type go -l
rg 'format!.*SELECT' --type rust -l

# Command injection variants
rg 'os\.system\(' --type py -l
rg 'exec\(' --type ts -l
rg 'exec\.Command\(' --type go -l
rg 'Command::new\(' --type rust -l

# Path traversal variants
rg 'filepath\.Join\(' --type go -l
rg 'path\.join\(' --type ts -l
rg 'os\.path\.join\(' --type py -l
```

#### Strategy B: Semgrep (AST-aware)

Higher precision than text search. Understands language structure.

Write a semgrep rule that captures the abstract pattern from Step 2:

```yaml
rules:
  - id: variant-sql-interpolation
    patterns:
      - pattern-either:
          - pattern: $DB.query(`...${$VAR}...`)
          - pattern: $DB.query("..." + $VAR + "...")
          - pattern: $DB.execute(`...${$VAR}...`)
    languages: [typescript, javascript]
    severity: ERROR
    message: "SQL injection variant -- use parameterized queries"
```

Run against the full codebase:
```bash
semgrep --config /tmp/variant-rule.yaml --json .
```

#### Strategy C: Data flow analysis

For complex patterns where the source and sink are in different functions.
Semgrep Pro supports cross-function taint tracking:

```yaml
rules:
  - id: taint-sql-injection
    mode: taint
    pattern-sources:
      - pattern: req.query.$PARAM
      - pattern: req.body.$PARAM
      - pattern: req.params.$PARAM
    pattern-sinks:
      - pattern: $DB.query($SQL, ...)
    pattern-sanitizers:
      - pattern: sanitize(...)
      - pattern: parseInt(...)
    languages: [typescript]
    severity: ERROR
```

#### Strategy D: Manual audit of related code

When automated tools cannot express the pattern:
1. Find all callers of the vulnerable function
2. Find all implementations of the same interface
3. Check copy-pasted code (same developer, same time period)
4. Check similar features (if user search has SQLi, check product search too)

### Step 4: Verify

For each candidate found in Step 3, confirm whether it is exploitable:

1. **Trace the data flow** from source to sink. Is the input truly attacker-controlled?
2. **Check for sanitization** between source and sink. Is there validation that
   prevents exploitation?
3. **Assess exploitability** -- can you construct a payload that reaches the sink
   in a dangerous state?
4. **Classify** as CONFIRMED, FALSE POSITIVE, or NEEDS INVESTIGATION.

## Variant Analysis Checklist

When you find a vulnerability, answer these questions to maximize variant discovery:

- [ ] What is the abstract pattern (source -> sink without sanitization)?
- [ ] Does the same developer have other code with the same pattern?
- [ ] Are there copy-pasted versions of this code elsewhere?
- [ ] Does the framework/library have a safe alternative that should have been used?
- [ ] Are there wrapper functions that claim to be safe but are not?
- [ ] Do other endpoints/handlers follow the same anti-pattern?
- [ ] Is the same pattern present in a different language in this codebase?
- [ ] Are there tests that exercise this code path with malicious input?

## Example: Full Variant Analysis

Initial finding: SSRF in `/api/preview` endpoint.

```python
# Found in routes/preview.py
@app.post("/api/preview")
async def preview(url: str):
    resp = await httpx.get(url)  # SSRF -- can hit internal services
    return {"content": resp.text}
```

**Characterize**: Any HTTP client call where the URL comes from user input
without validation against internal IP ranges.

**Search**:
```bash
# Find all httpx/requests/urllib usage
rg 'httpx\.(get|post|put|delete|request)\(' --type py -l
rg 'requests\.(get|post|put|delete)\(' --type py -l
rg 'urllib\.request\.urlopen\(' --type py -l

# Find all routes that accept URL parameters
rg 'def.*\(.*url.*:.*str' --type py -l
```

**Results** (hypothetical):
```
routes/preview.py:15     -- CONFIRMED (original finding)
routes/webhook.py:42     -- CONFIRMED (same pattern, webhook URL from user)
routes/import.py:28      -- FALSE POSITIVE (URL from admin config, not user input)
services/crawler.py:91   -- CONFIRMED (URL from database, originally user-supplied)
utils/og_parser.py:12    -- CONFIRMED (OpenGraph URL from user-submitted content)
```

Four confirmed variants from one initial finding. Without variant analysis, three
of these would have shipped to production unpatched.

## Integrating with Audit Reports

When reporting variant analysis results, structure as:

```markdown
### Finding: SSRF via unvalidated URL fetch
**Severity**: HIGH
**CWE**: CWE-918
**Initial location**: routes/preview.py:15

#### Variant analysis
| Location | Status | Notes |
|----------|--------|-------|
| routes/preview.py:15 | CONFIRMED | Original finding |
| routes/webhook.py:42 | CONFIRMED | Same pattern |
| services/crawler.py:91 | CONFIRMED | Indirect user input via DB |
| utils/og_parser.py:12 | CONFIRMED | URL from user content |
| routes/import.py:28 | FALSE POSITIVE | Admin-only config |

#### Recommended fix
Centralize URL validation in a shared utility and call it at every HTTP client site.
```
