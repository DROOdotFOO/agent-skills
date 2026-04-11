---
title: Security Scan Patterns
impact: CRITICAL
impactDescription: Missing a security vulnerability in review can lead to exploitation in production
tags: security,injection,xss,auth,secrets,polyglot
---

# Security Scan Patterns

Pattern-based checks for common vulnerabilities across languages. Run these against changed files and any files in the blast radius.

## Hardcoded Secrets

Grep for credentials committed to source:

```
# API keys, tokens, passwords
/(api[_-]?key|secret|token|password|credential)\s*[:=]\s*["'][^"']{8,}/i
/AKIA[0-9A-Z]{16}/                    # AWS access key
/ghp_[a-zA-Z0-9]{36}/                 # GitHub personal access token
/sk-[a-zA-Z0-9]{48}/                  # OpenAI API key
/-----BEGIN (RSA |EC )?PRIVATE KEY-----/
```

Check that `.env`, `.env.*`, `credentials.*`, and `*secret*` files are in `.gitignore`.

## SQL Injection

Look for string interpolation in SQL queries:

```python
# WRONG (Python)
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
cursor.execute("SELECT * FROM users WHERE id = " + user_id)

# CORRECT
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

```go
// WRONG (Go)
db.Query("SELECT * FROM users WHERE id = " + id)
db.Query(fmt.Sprintf("SELECT * FROM users WHERE id = %s", id))

// CORRECT
db.Query("SELECT * FROM users WHERE id = $1", id)
```

```typescript
// WRONG (TypeScript)
db.query(`SELECT * FROM users WHERE id = ${userId}`)

// CORRECT
db.query("SELECT * FROM users WHERE id = $1", [userId])
```

```elixir
# WRONG (Elixir)
Repo.query("SELECT * FROM users WHERE id = #{id}")

# CORRECT
Repo.query("SELECT * FROM users WHERE id = $1", [id])
from(u in User, where: u.id == ^id)
```

## XSS (Cross-Site Scripting)

```typescript
// WRONG
element.innerHTML = userInput
dangerouslySetInnerHTML={{ __html: userInput }}
document.write(userInput)

// Flag: any use of innerHTML, outerHTML, dangerouslySetInnerHTML, document.write
// with non-sanitized input
```

## Auth Bypass

Flag these patterns for manual review:

- Endpoints missing auth middleware/decorator
- `@public`, `skip_auth`, `allow_unauthenticated` on sensitive routes
- Role checks using string comparison instead of enum
- JWT verification disabled or secret hardcoded
- `verify=False` or `insecure_skip_verify` in TLS config

```python
# Flag: disabled TLS verification
requests.get(url, verify=False)
```

```go
// Flag: skipped TLS verification
&tls.Config{InsecureSkipVerify: true}
```

## Prototype Pollution (JavaScript/TypeScript)

```typescript
// WRONG -- deep merge without prototype check
function merge(target, source) {
  for (const key in source) {
    target[key] = source[key]  // allows __proto__ injection
  }
}

// Flag: Object.assign with user input, lodash.merge < 4.17.21
// Flag: recursive merge functions without hasOwnProperty check
```

## Path Traversal

```python
# WRONG
open(os.path.join(base_dir, user_supplied_path))

# Flag: file operations where the path includes user input
# without os.path.realpath + startswith validation
```

```go
// WRONG
filepath.Join(baseDir, userPath)  // does not prevent ../

// CORRECT
cleaned := filepath.Clean(userPath)
full := filepath.Join(baseDir, cleaned)
if !strings.HasPrefix(full, baseDir) { return error }
```

## Eval / Exec / Command Injection

```python
# CRITICAL: flag any use with non-literal arguments
eval(user_input)
exec(user_input)
os.system(user_input)
subprocess.call(user_input, shell=True)
```

```javascript
// CRITICAL
eval(userInput)
new Function(userInput)
child_process.exec(userInput)  // use execFile with args array instead
```

```go
// CRITICAL
exec.Command("sh", "-c", userInput)  // use exec.Command(binary, args...) instead
```

```elixir
# CRITICAL
System.cmd("sh", ["-c", user_input])  # pass args as list, never interpolate
Code.eval_string(user_input)
```

## Solidity-Specific

```solidity
// Reentrancy: external call before state update
function withdraw(uint amount) {
    msg.sender.call{value: amount}("");  // WRONG: call before state change
    balances[msg.sender] -= amount;
}

// Flag: tx.origin for auth (use msg.sender)
// Flag: unchecked return values on .call/.send/.transfer
// Flag: missing access control on state-changing functions
```

## Rust-Specific

```rust
// Flag: unsafe blocks -- require justification comment
unsafe { /* must document why this is sound */ }

// Flag: unwrap() on user-facing paths (use ? or expect with context)
let val = input.parse::<u64>().unwrap();  // WRONG in production code
```

## Scan Procedure

1. Run pattern matching on all changed files
2. Run pattern matching on files in CRITICAL blast radius
3. For each match, verify it is a true positive (not a false positive from tests, comments, or sanitized paths)
4. Classify each finding as MUST FIX (exploitable) or SHOULD FIX (defense in depth)
5. Report with file path, line number, vulnerability class, and recommended fix
