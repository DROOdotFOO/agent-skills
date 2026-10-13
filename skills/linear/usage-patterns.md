---
impact: HIGH
impactDescription: "Tool sequences for the common Linear workflows; keeps writes reviewable and idempotent"
tags: "linear,mcp,workflows,issues,projects"
---

## Resolve before writing

Every workflow starts the same way:

1. `get_workspace` -> confirm the workspace.
2. `list_teams` -> team key/ID. `list_issue_statuses(team)` -> state names.
3. `list_users(query)` when assigning; `list_issue_labels(team)` before labelling.
4. `list_issues(query=..., team=...)` to detect an existing issue before creating one.

## Create an issue from findings

```
save_issue(team="ENG", title="...", description="<markdown>",
           priority=2, labels=["Bug"], assignee="me", links=[{url, title}])
```

- `description` is raw Markdown with literal newlines; do not escape.
- Sub-issues: create the parent first, then children with `parentId=<key>`.
- Relations (`blocks`, `blockedBy`, `relatedTo`) are append-only; use the
  `remove*` counterparts to detach.
- Use `template=` instead of `title` to apply a team template server-side.

## Update an issue

```
save_issue(id="LIN-123", state="In Progress", addLabels=["Needs Review"])
save_issue(id="LIN-123", patch=[...])   # anchored partial description edits
```

`patch` applies atomically; one failing anchor aborts the whole save. Prefer
`patch` over resending `description` for long bodies.

## Standup notes -> comments

1. Extract issue keys and strong title/owner matches from the notes.
2. `get_issue(id)` for each candidate to confirm the match.
3. Present the planned `save_comment(issueId, body)` list; apply only after approval.
4. Return unmatched notes separately rather than guessing.

## Plan -> project

1. `save_project(name, summary, description, addTeams=[team], targetDate)`.
2. `save_milestone(project, name, targetDate)` only where the plan implies phases.
3. `save_issue(..., project=<project>, milestone=<name>)` per work item.
4. Link dependencies with `blockedBy`; do not invent structure the source lacks.

Show the whole tree before step 1.

## Cycle or timeframe report

```
list_cycles(teamId, type="previous")
list_issues(team, cycle=<number>, state="completed", limit=250, fields=[...])
```

Group by project/label; note in-flight work separately so progress is not
overstated. For arbitrary windows use `updatedAt="-P7D"` instead of a cycle.

## Bug investigation -> comment

`get_issue(id, includeRelations=true)` -> `list_comments(issueId)` ->
`get_attachment(id, format="url")` / `extract_images(markdown)` for screenshots
-> investigate in the repo -> one `save_comment` with the evidence-backed summary.

## Inbox triage

`get_notifications(unreadOnly=true)` -> act -> `mark_notification(id, read=true)`
or `snoozedUntilAt`.

## Pagination and limits

- `limit` max 250; follow `cursor` while `hasNextPage`.
- Use `fields` to keep large lists small; omit to get the default shape.
- `query` cannot be combined with `customView`.
