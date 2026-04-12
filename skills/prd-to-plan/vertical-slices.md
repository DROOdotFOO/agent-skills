---
title: Vertical Slice Philosophy
impact: CRITICAL
impactDescription: >
  Core methodology -- misunderstanding vertical slices produces plans that
  defer integration risk and delay feedback.
tags: vertical-slices, planning, architecture, phasing
---

# Vertical Slices

A vertical slice cuts through every layer of the stack to deliver one thin
piece of end-to-end functionality. The opposite -- a horizontal slice -- builds
out one full layer before touching the next.

## What Makes a Good Slice

A slice is good when it satisfies all four properties:

1. **Thin.** It touches the minimum surface area needed to deliver one
   behavior. If you can remove a table, an endpoint, or a UI element and the
   slice still works, it was too thick.

2. **End-to-end.** It crosses every boundary the feature will eventually cross:
   data store, business logic, API surface, and user interface. A slice that
   only adds database tables is not end-to-end.

3. **Demoable.** You can show it to a stakeholder and they can see something
   working. "I added three migration files" is not demoable. "You can now
   create a draft invoice from the dashboard" is demoable.

4. **Independent.** Later slices may build on earlier ones, but each slice
   stands on its own as a working increment. If removing a later slice would
   break an earlier one, the dependency runs the wrong direction.

## How to Identify Slice Boundaries

Start from user stories in the PRD. Each story is a candidate slice. Then ask:

- Can this story be split further while remaining demoable?
- Does this story depend on another story being finished first?
- Can I reorder these stories without breaking anything?

Group tightly coupled stories into one slice only when splitting them would
require significant throwaway scaffolding. The goal is to minimize the time
between "nothing works" and "one thing works."

## Ordering Slices

1. **Foundational slices first.** If slice B reads data that slice A writes,
   slice A comes first. Follow the data flow.
2. **Riskiest slices early.** If a slice involves an unfamiliar third-party API
   or a novel algorithm, schedule it early. Late surprises are expensive.
3. **Happy path before edge cases.** The first slice for a feature covers the
   simplest success case. Error handling, validation, and edge cases come in
   subsequent slices.

## Good vs Bad Slicing

### Bad: Horizontal Slices

```
Phase 1: Create all database tables and migrations
Phase 2: Build all API endpoints
Phase 3: Build all UI components
Phase 4: Wire everything together
Phase 5: Add error handling
```

Problems:

- Nothing is demoable until Phase 4.
- Integration bugs hide until late.
- Each phase is large and hard to review.
- Changing requirements invalidate multiple phases.

### Good: Vertical Slices

```
Phase 1: User can create a blank invoice (DB + API + minimal UI)
Phase 2: User can add line items to an invoice
Phase 3: User can send an invoice via email (email integration)
Phase 4: User can view invoice payment status (payment provider integration)
Phase 5: User can filter and search past invoices
```

Properties:

- Every phase is demoable from Phase 1.
- Integration with external services happens incrementally.
- Each phase is small enough to review in one sitting.
- Requirements changes only invalidate the affected slice.

### Bad: Too-Thick Slice

```
Phase 1: Full invoice management (create, edit, delete, send, track payments,
         generate PDF, search, filter, export CSV, role-based access)
```

This is not a slice, it is the entire feature. Split until each phase has 3-5
acceptance criteria.

### Good: Thin Slice from the Same Feature

```
Phase 1: Create a blank invoice with a title and due date.
         - POST /invoices creates a record
         - GET /invoices/:id returns the invoice
         - UI shows a form and displays the saved invoice
```

Three acceptance criteria. One session of work. Demoable.
