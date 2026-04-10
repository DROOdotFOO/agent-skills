---
name: grill-me
description: >
  Interview the user relentlessly about a plan or design until reaching shared understanding.
  TRIGGER when: user wants to stress-test a plan, get grilled on their design, or says "grill me".
  DO NOT TRIGGER when: user asks for feedback on code (use code-review), or wants a simple review.
metadata:
  author: mattpocock
  version: "1.0.0"
  tags: interview, design-review, planning, stress-test
  license: MIT
---

# Grill Me

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

## What You Get

- Exhaustive interrogation of every design decision
- Recommended answers for each question
- Dependencies between decisions resolved in order
- Shared understanding of the full design space

## Rules

1. Ask questions **one at a time**
2. For each question, provide your **recommended answer**
3. If a question can be answered by **exploring the codebase**, explore the codebase instead
4. Walk down each branch of the decision tree, resolving dependencies between decisions
5. Continue until we reach shared understanding on all branches
