# prepper

Pre-session context builder that generates a project briefing before starting work. Gathers git activity, GitHub state, dependency status, CI results, and recall context into a single markdown document.

## Status: MVP

## Install

```bash
cd agents/prepper
pip install -e ".[dev]"
```

## CLI

```bash
prepper brief                              # briefing for current directory
prepper brief /path/to/repo                # briefing for specific repo
prepper brief --repo owner/repo            # include GitHub state
prepper brief --project myproj             # include recall context
prepper brief --output briefing.md         # write to file
prepper brief --raw                        # raw markdown output
prepper inject                             # write to .claude/prepper-briefing.md
prepper inject --repo owner/repo --project myproj
```

## Gatherers

| Gatherer | Source | Priority |
|----------|--------|----------|
| Git Activity | `git log`, `git status`, `git branch` | high |
| GitHub State | `gh pr list`, `gh issue list`, `gh run list` | high |
| CI Status | `gh run list --limit 1` | medium |
| Recall Context | recall store (if installed) | medium |
| Dependency Status | npm/pip/mix/go audit and outdated | low |

All gatherers handle missing tools gracefully -- if `gh` or `git` is not installed, those sections are skipped.

## Session Injection

`prepper inject` writes the briefing to `.claude/prepper-briefing.md` in the repo root, where Claude Code can pick it up as session context.

## Tests

```bash
cd agents/prepper
python -m pytest tests/ -v
```
