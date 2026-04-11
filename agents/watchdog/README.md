# watchdog

Continuous repo health monitor. Scans GitHub repos for stale PRs, failing CI, dependency vulnerabilities, TODOs referencing closed issues, and stale assigned issues. Outputs markdown reports.

Requires the [GitHub CLI](https://cli.github.com/) (`gh`) to be installed and authenticated.

## Status: MVP

## Install

```bash
cd agents/watchdog
pip install -e ".[dev]"
```

## CLI

```bash
# Scan a single repo
watchdog scan owner/repo

# Scan a local repo (checks TODOs and lockfile audit)
watchdog scan owner/repo --path /path/to/local/clone

# Scan multiple repos
watchdog scan owner/repo1 owner/repo2

# Scan and write markdown report to file
watchdog report owner/repo -o health-report.md

# Continuous monitoring (default: every 60 minutes)
watchdog watch owner/repo --interval 60

# Use a config file
watchdog scan --config watchdog.toml
```

## Checks

| Check | What it does |
|-------|-------------|
| `stale_prs` | PRs open longer than threshold (default 14 days) |
| `ci_status` | Recent CI workflow run failures |
| `open_issues_age` | Assigned issues older than threshold (default 30 days) |
| `todo_closed_refs` | TODOs referencing closed GitHub issues |
| `lockfile_audit` | npm audit / pip-audit / cargo-audit / mix_audit |
| `security_advisories` | Dependabot / vulnerability alerts |

## Config file

Optional `watchdog.toml`:

```toml
[[repos]]
name = "owner/repo"
path = "/path/to/local/clone"  # optional

[thresholds]
stale_pr_days = 14
stale_issue_days = 30

[schedule]
interval_minutes = 60
```

## Tests

```bash
cd agents/watchdog
python -m pytest tests/ -v
```
