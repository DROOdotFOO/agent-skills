---
title: Adversarial Personas
impact: HIGH
impactDescription: Three hostile review personas with self-review techniques for catching issues that standard reviews miss
tags: review, personas, adversarial, self-review
---

# Adversarial Personas

## The Saboteur

Goal: find what breaks in production under real-world conditions.

**Focus areas:**

- **Race conditions** -- What happens under concurrent access? Are shared resources properly synchronized? Can two requests hit the same state simultaneously?
- **Edge cases** -- Empty inputs, maximum values, unicode, negative numbers, nil/null/undefined where unexpected. What are the boundary conditions?
- **Resource exhaustion** -- Unbounded allocations, missing timeouts, connection pool leaks, file handle accumulation. What happens at scale?
- **Cascading failures** -- If this component fails, what else breaks? Are there circuit breakers? What does partial failure look like?
- **State corruption** -- Can interrupted operations leave inconsistent state? Are multi-step mutations atomic? What if the process dies mid-operation?

**Questions to ask:**

- What happens if this is called 10,000 times per second?
- What if the dependency returns after 30 seconds instead of 30ms?
- What if the input is 100MB instead of 100 bytes?
- What if this runs on a machine with 256MB of RAM?

## The New Hire

Goal: find what makes the code unmaintainable for someone seeing it for the first time.

**Focus areas:**

- **Unclear naming** -- Variables named `x`, `tmp`, `data`, `result`. Functions that don't describe their behavior. Boolean parameters without names.
- **Missing documentation** -- No explanation of WHY, only WHAT. Missing contract descriptions (what are the preconditions? postconditions? invariants?).
- **Implicit assumptions** -- Code that only works because of some non-obvious external condition. Hidden dependencies on execution order, environment variables, or global state.
- **Magic numbers** -- Hardcoded values without explanation. Timeouts, retry counts, buffer sizes, thresholds that appear from nowhere.
- **Complex setup** -- How many steps to run this locally? How many undocumented prerequisites? Would onboarding take hours or days?
- **Cognitive load** -- Functions longer than a screen. Deeply nested conditionals. Clever tricks that require pausing to understand.

**Questions to ask:**

- Can I understand this function without reading any other file?
- If I change this, how do I know what I might break?
- Where is the entry point and how do I trace the flow?
- What would I search for if this broke at 2am?

## The Security Auditor

Goal: find the attack surface using OWASP-informed threat modeling.

**Focus areas:**

- **Injection** -- SQL, command, template, LDAP, XPath injection. Any place user input reaches an interpreter without sanitization.
- **Auth bypass** -- Missing authentication checks, broken access control, IDOR (insecure direct object references), JWT misuse, session fixation.
- **Data exposure** -- Secrets in logs, PII in error messages, sensitive data in URLs, overly permissive API responses, missing field-level access control.
- **Privilege escalation** -- Can a regular user perform admin actions? Are role checks enforced at every layer or just the UI?
- **SSRF** -- Can user input control outbound requests? URL parsing inconsistencies? Internal service endpoints reachable from user input?
- **Path traversal** -- Can user input escape intended directories? Are file paths properly sanitized? Symlink following?
- **Deserialization** -- Untrusted data deserialized without validation? Pickle, YAML.load, JSON.parse with reviver functions?
- **Timing attacks** -- Non-constant-time comparisons on secrets? Observable timing differences in auth flows?

**Questions to ask:**

- What is the trust boundary? Where does untrusted input enter?
- If I control this input, what is the worst I can achieve?
- Are there any paths that skip authorization checks?
- What happens if I replay this request? Send it twice? Send it malformed?

## Self-Review Techniques

Apply these before running the personas to prime your adversarial mindset:

1. **Read bottom-up** -- Start from the last function and work upward. This breaks the author's narrative flow and forces you to evaluate each unit independently.
2. **State the contract before reading the body** -- Look at the function signature and name. Write down what you expect it to do. Then read the body. Mismatches between expectation and reality are bugs or naming problems.
3. **Assume everything can be null** -- For every variable access, ask: can this be nil/null/undefined at this point? Trace back to confirm.
4. **Invert every condition** -- For every if/else, ask: what happens in the else branch? Is it handled? Is it even reachable? Dead code hides bugs.
5. **Follow the error path** -- Ignore the happy path entirely. Only trace what happens when things fail. Are errors caught? Logged? Propagated? Swallowed?
