# Scribe

Session insight extractor. Watches Claude Code sessions and writes structured insights to the recall knowledge store. Closes the knowledge loop by continuously extracting decisions, corrections, preferences, and patterns from session data.

## Install

```bash
cd agents/scribe && pip install -e ".[dev]"
```

## Usage

```bash
scribe watch [--once] [--idle-minutes 10]   # continuous watch
scribe analyze <session-id> --project PATH   # analyze one session
scribe stats [--days 30]                     # activity statistics
scribe recent [--limit 10]                   # recent insights
scribe serve                                 # MCP server (stdio)
```

## How It Works

1. **Session discovery**: Tails `~/.claude/history.jsonl` with byte-offset tracking to find active sessions
2. **Idle detection**: Sessions with no new messages for N minutes (default 10) are analyzed
3. **Rich parsing**: Reads full session JSONL (`~/.claude/projects/{key}/{sid}.jsonl`) -- tool calls, file edits, bash commands, not just user prompts
4. **Analysis**: Tool usage profiling, files touched, commands run/failed, correction detection, preference detection
5. **Classification**: Enhanced beyond recall extract -- corrections, preferences, decisions, gotchas, tool usage patterns
6. **Deduplication**: FTS5 search + Jaccard token overlap against existing recall entries
7. **Storage**: Writes to recall store (with AARTS hook protection), logs activity to `~/.local/share/scribe/activity.jsonl`

## MCP Server

```json
{"mcpServers": {"scribe": {"command": "scribe", "args": ["serve"]}}}
```

Tools: `scribe_status`, `scribe_stats`, `scribe_recent`

## Tests

```bash
python -m pytest tests/ -v   # 114 tests, 0 mocks
```
