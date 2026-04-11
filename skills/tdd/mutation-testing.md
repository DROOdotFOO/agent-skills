---
title: Mutation Testing
impact: MEDIUM
impactDescription: Mutation testing reveals gaps that code coverage metrics miss
tags: mutation-testing, test-quality, coverage
---

# Mutation Testing

Code coverage tells you what code ran. Mutation testing tells you whether your tests would **catch a bug**. A mutant is a small change to your code (flip a conditional, change `+` to `-`, remove a statement). If all tests still pass, the mutant "survived" -- your tests have a gap.

## Tools by Language

| Language | Tool | Install | Run |
|----------|------|---------|-----|
| TypeScript/JS | Stryker | `npm i -D @stryker-mutator/core` | `npx stryker run` |
| Python | mutmut | `pip install mutmut` | `mutmut run` |
| Rust | cargo-mutants | `cargo install cargo-mutants` | `cargo mutants` |
| Java/Kotlin | PIT | Maven/Gradle plugin | `mvn test-compile org.pitest:pitest-maven:mutationCoverage` |
| Elixir | muzak | `{:muzak, "~> 1.0", only: :test}` | `mix muzak` |
| Go | gremlins | `go install github.com/go-gremlins/gremlins/cmd/gremlins@latest` | `gremlins unleash` |

## Interpreting Results

- **Killed mutant**: Your test suite detected the change. Good.
- **Survived mutant**: No test caught the change. You have a gap.
- **Timed out mutant**: The mutation caused an infinite loop. Usually counts as killed.
- **Equivalent mutant**: The mutation doesn't change behavior (e.g., `x * 1` -> `x * 1`). Ignore these.

Focus on **survived mutants**. Each one is a concrete behavior your tests do not verify. Write a test that would catch it, then re-run.

## Mutation Score

`mutation_score = killed / (killed + survived)`

- Below 60%: significant test gaps
- 60-80%: acceptable for most projects
- Above 80%: strong suite, diminishing returns beyond this

## When Mutation Testing Is Worth It

**Worth it:**
- Core business logic (payment, auth, data transformation)
- Libraries consumed by others
- Code where bugs have high cost (financial, security)

**Skip it:**
- Glue code / thin wrappers
- UI rendering tests
- Prototypes and throwaway code
- Very large codebases (run on critical modules only)

## Workflow Integration

Run mutation testing **after** the TDD cycle is complete, not during. It is a validation step, not a development step.

1. Finish the TDD incremental loop
2. Run mutation testing on the module you just built
3. For each survived mutant, add a test
4. Re-run until satisfied with the score
