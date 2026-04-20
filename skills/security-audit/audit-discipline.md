---
title: Audit Discipline
impact: CRITICAL
impactDescription: Rationalizing away findings and skipping proof requirements causes the most dangerous false negatives in application security audits
tags: security, audit, discipline, anti-skip, proof, false-negatives, context-first
---

# Audit Discipline

Rules that prevent the most common audit failure modes: dismissing real
findings through rationalization, reporting theoretical vulnerabilities
without proof, and scanning before understanding.

## Context-First Rule

Before hunting vulnerabilities, understand the code. The sequence is:

1. **Comprehend** -- Read the code to understand what it does and why
2. **Hypothesize** -- Based on understanding, identify where bugs could hide
3. **Verify** -- Confirm or disprove each hypothesis with evidence

Never: scan -> flag -> move on. That produces noise, not findings.

Minimum comprehension before vulnerability hunting:
- Can you explain the application's authentication flow in one paragraph?
- Can you draw the trust boundaries (what is internal vs external)?
- Can you name the 3 most sensitive operations (data access, money movement, privilege changes)?

If you cannot answer these, you are not ready to audit.

## Rationalizations to Reject

Every rationalization below has led to missed vulnerabilities in production.

| Rationalization | Why It Is Wrong | Required Action |
|---|---|---|
| "Input is validated at the API gateway" | Gateways change. Internal services call each other directly. A single misconfigured route bypasses the gateway entirely. | Validate at every trust boundary. Defense in depth, not defense at perimeter. |
| "Only admins can access this endpoint" | Admin credentials get stolen. SSRF bypasses authentication entirely. Internal network access skips auth. | Audit every endpoint as if it were publicly accessible. Document required auth explicitly. |
| "The ORM prevents injection" | ORMs have raw query escapes (`Sequelize.literal`, `RawSQL`, `gorm.Raw`). Developers use them. ORM-specific injection exists (NoSQL, LDAP). | Grep for raw query usage alongside ORM calls. Both coexist in most codebases. |
| "HTTPS encrypts the data" | HTTPS protects transit only. Data is logged in plaintext. Error messages expose it. It sits unencrypted in memory, caches, and databases. | Trace data after decryption: where is it stored, logged, cached, serialized? |
| "We sanitize on output" | Output encoding must match the exact context (HTML body vs attribute vs JS vs URL vs SQL). One context mismatch = bypass. | Verify sanitization matches every output context. HTML encoding does not prevent JS injection in `<script>` blocks. |
| "Rate limiting stops brute force" | Rate limits are per-IP. Distributed attacks, IPv6 rotation, and credential stuffing with unique IPs bypass them trivially. | Rate limit AND fix the underlying vulnerability. Rate limiting is mitigation, not remediation. |

## Proof-Required Discipline

Every finding at MEDIUM severity or above MUST include a concrete exploit
demonstration. Theoretical findings waste defender time and erode trust in
the audit.

**FINDING** (has proof):
```
## [H-1] SQL Injection in user search endpoint

Endpoint: GET /api/users?q=test
Payload: GET /api/users?q=' OR '1'='1' --
Expected: 400 Bad Request or sanitized query
Actual: 200 OK with all 15,847 user records returned
Impact: Full database read access for unauthenticated attacker

Vulnerable code: src/routes/users.ts:47
  const results = await db.query(`SELECT * FROM users WHERE name LIKE '%${req.query.q}%'`);
```

**LEAD** (no proof -- needs investigation):
```
## [LEAD] Possible SQL injection in user search

The search endpoint appears to concatenate user input into a SQL query
but exploitation has not been verified.
```

Rules:
- No proof = LEAD. LEADs go in appendix, not findings section.
- Proof must include: endpoint/location, payload, expected vs actual behavior.
- For code-only review (no running instance): proof is the exact input that triggers the vulnerable path, traced through the code.
- "Could be exploited" or "may be vulnerable" is never acceptable for MEDIUM+.

## False-Positive Elimination Pass

After completing vulnerability scanning (Phase 2), run this pass on every
MEDIUM+ finding before reporting:

### For each finding:

1. **Trace source-to-sink**: Is there an unbroken path from attacker-controlled
   input to the vulnerable operation? Map every transformation along the way.

2. **Verify attacker control**: Does the attacker actually control the input
   at the source? (Not all request parameters are user-controlled -- some are
   set by middleware, session, or server-side logic.)

3. **Check sanitization**: Is there ANY sanitization, encoding, validation,
   or type coercion between source and sink that would prevent exploitation?

4. **Craft payload**: Construct the specific input that exploits the
   vulnerability given all intermediate transformations.

5. **Classify**:
   - **CONFIRMED**: Payload constructed, path verified end-to-end
   - **FALSE POSITIVE**: Sanitization exists between source and sink (document which)
   - **NEEDS INVESTIGATION**: Path exists but one hop is unclear

### Decision tree:

```
Attacker controls input? --NO--> FALSE POSITIVE
        |
       YES
        |
Input reaches sink without sanitization? --NO--> FALSE POSITIVE (document sanitizer)
        |
       YES
        |
Payload bypasses any remaining defenses? --NO--> FALSE POSITIVE (document defense)
        |
       YES
        |
    CONFIRMED
```

## Threat Personas

Use these three personas to structure your attack surface analysis:

### External Attacker (unauthenticated)
- Controls: HTTP requests, headers, query params, file uploads, WebSocket messages
- Cannot: access internal endpoints, read server state, modify config
- Goals: RCE, data exfiltration, account takeover, DoS
- Test: Every public endpoint with malicious input

### Authenticated User (authorized but malicious)
- Controls: all of the above + valid session, own account data
- Cannot: access other users' data, escalate privileges, modify system config
- Goals: privilege escalation, IDOR, data of other users, business logic abuse
- Test: Every authenticated endpoint with other users' IDs, role boundaries

### Compromised Dependency (supply chain)
- Controls: code execution within the application's process, read env vars, filesystem access
- Cannot: (initially) make network calls if egress is filtered
- Goals: exfiltrate secrets, establish persistence, pivot to other services
- Test: What damage can arbitrary code in node_modules/site-packages do?

Each finding should note which persona can exploit it. A vulnerability
requiring the compromised-dependency persona is less severe than one
exploitable by an external attacker (unless the dependency is widely used).
