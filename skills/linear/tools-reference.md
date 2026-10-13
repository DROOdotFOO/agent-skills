---
impact: HIGH
impactDescription: "Complete inventory of the hosted Linear MCP tools, captured live from tools/list; prevents calling tools that do not exist"
tags: "linear,mcp,tools,reference"
---

# Linear MCP tools reference

Source: `tools/list` against `https://mcp.linear.app/mcp` on 2026-10-13 (server `Linear MCP 1.0.0`).
68 tools on the read-write endpoint; 38 on `/mcp/readonly` (marked RO below). The server does not emit `listChanged`, so re-run `tools/list` when a tool is missing.

Conventions shared by most tools:

- Identifiers: issues accept `LIN-123` style keys or UUIDs; projects accept `P-ENG-123`, slug, name, or UUID; teams/users/labels/states accept name or ID; `assignee`/`creator` accept `"me"`.
- Lists paginate with `limit` (default 50, max 250) and `cursor`; results carry `hasNextPage`.
- Date filters (`createdAt`, `updatedAt`, `triagedAt`) take ISO-8601 dates or negative durations such as `-P1D`.
- `save_*` tools create when `id` is omitted and update when it is set. Never pass `id` on create.
- `fields` narrows the returned shape; explicitly requested empty fields return `null`.

## Workspace, teams, users

| Tool | RO | Purpose | Key arguments |
| --- | --- | --- | --- |
| `get_workspace` | yes | Retrieve the connected Linear workspace | - |
| `list_teams` | yes | List teams in the user's Linear workspace, including their parent IDs and hierarchy names | `limit`, `cursor`, `orderBy`, `query`, `parentTeam`, `ancestorTeam`, `includeArchived`, `createdAt` ... |
| `get_team` | yes | Retrieve details of a specific Linear team, including its parent ID and hierarchy name | `query` |
| `list_users` | yes | Retrieve users in the Linear workspace | `limit`, `cursor`, `orderBy`, `query`, `team` |
| `get_user` | yes | Retrieve details of a specific Linear user | `query` |
| `get_triage_responsibility` | yes | Retrieve who is responsible for a team's triage: the person on triage now, what happens when an issue enters triage, and the upcoming shifts of the team's triage rotation | `team`, `user`, `limit` |
| `get_notifications` | yes | Get a page of notifications from the authenticated user's Linear inbox | `limit`, `cursor`, `unreadOnly` |
| `mark_notification` | no | Mark a Linear inbox notification as read or unread, or snooze or unsnooze it | `id`, `read`, `snoozedUntilAt` |

## Issues

| Tool | RO | Purpose | Key arguments |
| --- | --- | --- | --- |
| `list_issues` | yes | List issues in the user's Linear workspace, including active Triage Intelligence suggestions for issues in triage | `limit`, `cursor`, `orderBy`, `query`, `customView`, `team`, `includeSubTeams`, `state` ... |
| `get_issue` | yes | Retrieve detailed information about an issue by ID, including attachments, git branch name, and active Triage Intelligence suggestions when the issue is in triage | `id`, `fields`, `includeRelations`, `includeCustomerNeeds`, `includeReleases` |
| `save_issue` | no | Create or update a Linear issue | `id`, `title`, `description`, `patch`, `team`, `template`, `cycle`, `milestone` ... |
| `share_issue` | no | Share an issue with a workspace user who cannot otherwise access it | `issue`, `user` |
| `unshare_issue` | no | Remove a workspace user's shared access to an issue | `issue`, `user` |
| `list_issue_statuses` | yes | List available issue statuses in a Linear team | `team` |
| `get_issue_status` | yes | Retrieve detailed information about an issue status in Linear by name or ID | `id`, `name`, `team` |

## Issue labels

| Tool | RO | Purpose | Key arguments |
| --- | --- | --- | --- |
| `list_issue_labels` | yes | List available issue labels in a Linear workspace or team | `limit`, `cursor`, `orderBy`, `name`, `team`, `includeArchived`, `includeGroups` |
| `save_issue_label` | no | Create or update a Linear issue label | `id`, `name`, `description`, `color`, `teamId`, `parent`, `isGroup`, `groupType` |
| `create_issue_label` | no | Create a new Linear issue label | `name`, `description`, `color`, `teamId`, `parent`, `isGroup` |
| `retire_issue_label` | no | Retire a Linear issue label so it cannot be applied to new issues | `id` |
| `restore_issue_label` | no | Restore a retired Linear issue label, making it available for use on issues again | `id` |

## Comments

| Tool | RO | Purpose | Key arguments |
| --- | --- | --- | --- |
| `list_comments` | yes | List comments on a Linear issue, project, initiative, document, project milestone, or project/initiative status update | `limit`, `cursor`, `orderBy`, `issueId`, `projectId`, `initiativeId`, `documentId`, `milestoneId` ... |
| `save_comment` | no | Create or update a comment on a Linear issue, project, initiative, document, project milestone, or project/initiative status update | `id`, `issueId`, `projectId`, `initiativeId`, `documentId`, `milestoneId`, `statusUpdateId`, `statusUpdateType` ... |
| `delete_comment` | no | Delete a Linear comment | `id` |

## Projects and milestones

| Tool | RO | Purpose | Key arguments |
| --- | --- | --- | --- |
| `list_projects` | yes | List projects in the user's Linear workspace | `limit`, `cursor`, `orderBy`, `customView`, `query`, `state`, `initiative`, `team` ... |
| `get_project` | yes | Retrieve details of a specific project in Linear | `query`, `includeCustomerNeeds`, `customerNeedsLimit`, `customerNeedsCursor`, `includeMilestones`, `includeMembers`, `includeResources` |
| `save_project` | no | Create or update a Linear project | `id`, `name`, `template`, `icon`, `color`, `summary`, `description`, `patch` ... |
| `list_milestones` | yes | List all milestones in a Linear project | `project` |
| `get_milestone` | yes | Retrieve details of a specific milestone by ID or name | `project`, `query` |
| `save_milestone` | no | Create or update a milestone in a Linear project | `project`, `id`, `name`, `description`, `targetDate` |
| `list_project_labels` | yes | List available project labels in a Linear workspace or team | `limit`, `cursor`, `orderBy`, `name`, `team`, `includeArchived`, `includeGroups` |
| `save_project_label` | no | Create or update a Linear project label | `id`, `name`, `description`, `color`, `teamId`, `parent`, `isGroup` |
| `retire_project_label` | no | Retire a Linear project label so it cannot be applied to new projects | `id` |
| `restore_project_label` | no | Restore a retired Linear project label, making it available for use on projects again | `id` |

## Cycles and views

| Tool | RO | Purpose | Key arguments |
| --- | --- | --- | --- |
| `list_cycles` | yes | Retrieve cycles for a specific Linear team | `teamId`, `type` |
| `list_custom_views` | yes | Find saved issue, project, and initiative views accessible to the user, including personal, workspace, and team views | `limit`, `cursor`, `orderBy`, `query`, `type`, `team`, `shared` |
| `list_templates` | yes | List the Linear issue, project, and document templates available to the authenticated user | `type`, `team` |
| `get_template` | yes | Retrieve a Linear template by ID or name: the content it pre-fills, the ids it applies, its sub-issues, and its form fields | `id` |

## Status updates

| Tool | RO | Purpose | Key arguments |
| --- | --- | --- | --- |
| `get_status_updates` | yes | List or get project/initiative status updates | `limit`, `cursor`, `orderBy`, `type`, `id`, `project`, `initiative`, `user` ... |
| `save_status_update` | no | Create or update a project/initiative status update | `type`, `id`, `project`, `initiative`, `body`, `health`, `isDiffHidden` |
| `delete_status_update` | no | Delete (archive) a project or initiative status update | `type`, `id` |

## Documents and attachments

| Tool | RO | Purpose | Key arguments |
| --- | --- | --- | --- |
| `list_documents` | yes | List documents in the user's Linear workspace | `limit`, `cursor`, `orderBy`, `query`, `projectId`, `initiativeId`, `teamId`, `creatorId` ... |
| `get_document` | yes | Retrieve a Linear document by ID or slug | `id` |
| `save_document` | no | Create or update a Linear document | `id`, `title`, `content`, `patch`, `project`, `issue`, `initiative`, `cycle` ... |
| `get_attachment` | yes | Retrieve an issue attachment by ID | `id`, `format` |
| `prepare_attachment_upload` | no | Prepare a direct Linear file upload for an existing issue | `issue`, `filename`, `contentType`, `size`, `title`, `subtitle` |
| `create_attachment_from_upload` | no | Link an already-uploaded Linear assetUrl to an existing issue as an attachment | `issue`, `assetUrl`, `title`, `subtitle` |
| `create_attachment` | no | Deprecated fallback for tiny files only | `issue`, `base64Content`, `filename`, `contentType`, `size`, `sha256`, `title`, `subtitle` |
| `delete_attachment` | no | Delete an attachment by ID | `id` |
| `extract_images` | yes | Extract and fetch images from markdown content | `markdown` |

## Releases

| Tool | RO | Purpose | Key arguments |
| --- | --- | --- | --- |
| `list_release_pipelines` | yes | List release pipelines in the workspace | `limit`, `cursor`, `orderBy`, `query`, `team`, `type`, `isProduction`, `includeStages` ... |
| `list_releases` | yes | List releases in the workspace, with optional filtering by pipeline, stage, version, and text | `limit`, `cursor`, `orderBy`, `query`, `pipeline`, `stage`, `stageType`, `version` ... |
| `get_release` | yes | Retrieve details of a release by ID or slug | `id`, `includeReleaseNotes` |
| `save_release` | no | Create or update a release | `id`, `name`, `description`, `version`, `pipeline`, `stage`, `startDate`, `targetDate` ... |
| `list_release_notes` | yes | List release notes in the workspace, optionally filtered by pipeline or covered release | `limit`, `cursor`, `orderBy`, `query`, `pipeline`, `release`, `includeContent`, `includeReleases` ... |
| `get_release_note` | yes | Retrieve release notes by ID or slug, including markdown content | `id`, `includeReleases` |
| `save_release_note` | no | Create or update release notes | `id`, `pipeline`, `title`, `content`, `patch`, `releases`, `rangeFromRelease`, `rangeToRelease` |

## Diffs (Linear code review)

| Tool | RO | Purpose | Key arguments |
| --- | --- | --- | --- |
| `get_diff` | yes | Exact lookup for a Linear diff | `urlOrId` |
| `list_diffs` | yes | List Linear diff pull requests visible to the authenticated user | `limit`, `cursor`, `orderBy`, `query`, `owner`, `repo`, `status`, `author` ... |
| `get_diff_threads` | yes | Exact lookup for diff threads and the authenticated user's drafts | `urlOrId`, `threadId`, `resolved`, `orderBy` |
| `save_diff_comment` | no | Create, reply to, or edit a comment or persisted draft on a Linear diff | `urlOrId`, `commentId`, `draftId`, `draft`, `parentId`, `body`, `anchor`, `anchorContent` |
| `resolve_diff_thread` | no | Resolve or reopen a top-level comment thread on a Linear diff | `threadId`, `resolved` |
| `delete_diff_comment` | no | Delete a comment or persisted draft from a Linear diff | `commentId`, `draftId` |
| `submit_diff_review` | no | Approve a Linear diff, request changes, or submit a review comment | `urlOrId`, `decision`, `body` |
| `update_diff` | no | Update a Linear diff's title, description, reviewer requests, issue links, or status | `urlOrId`, `title`, `description`, `addedReviewRequests`, `removedReviewRequests`, `addedIssueLinks`, `removedIssueLinks`, `statusAction` |
| `merge_diff` | no | Merge a Linear diff or add it to the repository's merge queue | `urlOrId`, `mergeMethod` |

## Agent skills and docs

| Tool | RO | Purpose | Key arguments |
| --- | --- | --- | --- |
| `list_agent_skills` | yes | List Linear Agent skills available to the authenticated user | `limit`, `cursor`, `orderBy` |
| `get_agent_skill` | yes | Retrieve a Linear Agent skill by ID, including its full markdown instructions | `id` |
| `search_documentation` | yes | Search Linear's documentation to learn about features and usage | `query`, `page` |

## Deprecated

- `create_attachment` (base64, tiny files only) -> use `prepare_attachment_upload` + `create_attachment_from_upload`.
- `create_issue_label` -> use `save_issue_label`.

## Guarded tools

`share_issue` / `unshare_issue` and every `*_diff*` write tool mutate access or code review state; the tool descriptions require an explicit user request. `merge_diff` merges or queues a PR.
