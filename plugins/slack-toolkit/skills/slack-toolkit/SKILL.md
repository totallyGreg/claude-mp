---
name: slack-toolkit
metadata:
  version: "1.1.0"
compatibility: Requires python3 for slacker.py CLI execution
license: MIT
description: >-
  Use this skill when the Slack MCP server is not connected, when you need
  Canvas read/update operations, when you need to add/remove reactions, or
  when direct Slack API access is explicitly requested. Triggers on "read
  slack canvas", "update slack canvas", "create slack canvas", "rewrite
  slack canvas", "add slack reaction", "remove slack reaction", "get slack
  thread", "slack channel history", "parse slack url", "slack without mcp",
  "slack api curl".
---

# Slack Toolkit

Direct Slack Web API access via Python CLI. Fills gaps in the official Slack MCP plugin (no Canvas read/update, no reactions) and provides a full fallback when MCP is unavailable.

> **Rule:** Check if the Slack MCP server is connected first. Use this skill only when MCP is unavailable or for operations MCP cannot perform (Canvas read/update, reactions).

## Configuration

| Variable | Source | Required |
|----------|--------|----------|
| `$SLACK_USER_TOKEN` | Env var or `keychainctl get SLACK_USER_TOKEN` | Yes (Canvas, reactions, threads) |
| `$SLACK_BOT_TOKEN` | Env var or `keychainctl get SLACK_BOT_TOKEN` | Optional (channel reads, bot actions) |

Token resolution: env var first, `keychainctl` fallback (macOS-only). Validates prefix (`xoxp-`/`xoxb-`).

## Enterprise Grid

All Slack conversation endpoints require **POST with form-encoded body**. GET returns `not_authed` on enterprise grids. The CLI handles this transparently.

## Canvas Types

Slack has two incompatible canvas backends. The type is determined at the **workspace level** — some workspaces (particularly Enterprise Grid) route all canvas creation through the legacy Quip backend, even when using the `canvases.create` API.

- **Quip-type** (`filetype: "quip"`): Legacy format. Read works (auto HTML→markdown). `canvases.edit` (append/replace) **does not work**. Content limited to ~4KB per create call. Inline comments not accessible via API.
- **New Canvas API** (all other filetypes): Full CRUD via `canvases.create`/`canvases.edit`. Auto-chunked for large content.

Run `canvas probe` to detect your workspace type before creating canvases. On quip workspaces, updating content requires creating a new canvas with the full content.

## CLI Reference

All commands: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/slack-toolkit/scripts/slacker.py <command> [args]`

### Canvas Operations (MCP gaps)

```bash
# Read canvas (auto-detects quip vs new-type, outputs markdown)
slacker.py canvas read <canvas_id>

# Create standalone canvas (always new-type)
slacker.py canvas create <title> --content "# Markdown content"
slacker.py canvas create <title> --content-file /path/to/file.md

# Update canvas — append from file (recommended for code blocks / large content)
slacker.py canvas update <canvas_id> --append-file /path/to/content.md

# Update canvas — append inline (small additions only)
slacker.py canvas update <canvas_id> --append "## New Section\n\nContent here"

# Update canvas — replace a section (requires section_id from read)
slacker.py canvas update <canvas_id> --replace <section_id> --content-file /path/to/content.md

# Rewrite quip canvas as new-type (creates new canvas, outputs both IDs)
slacker.py canvas rewrite <canvas_id>

# Detect workspace canvas type (quip vs new-type)
slacker.py canvas probe
```

Canvas content uses markdown. On non-quip workspaces, auto-chunks content >3KB. On quip workspaces, large content is truncated with a warning. See `references/canvas-operations.md` for details.

### Reactions (MCP gap)

```bash
slacker.py react <channel> <timestamp> <emoji_name>
slacker.py unreact <channel> <timestamp> <emoji_name>
```

Emoji name without colons (e.g., `thumbsup` not `:thumbsup:`).

### Threads & History (MCP fallback)

```bash
# Full thread with pagination
slacker.py thread <channel> <thread_ts> [--limit 200]

# Channel history
slacker.py history <channel> [--limit 100]

# Parse Slack URL to channel + timestamp
slacker.py parse-url "https://workspace.slack.com/archives/C0123/p1768255289788089"
```

### Common Flags

| Flag | Description |
|------|-------------|
| `--bot` | Use bot token instead of user token |
| `--limit N` | Max messages to retrieve (default: 200 threads, 100 history; hard cap: 1000) |

## Output Contract

- **stdout**: JSON (compact, parseable) or markdown (canvas read)
- **stderr**: Human-readable errors
- **Exit codes**: 0=success, 1=usage, 2=auth, 3=API error, 4=rate limited

## Thread URL Parsing

Two formats supported:
- `https://<workspace>.slack.com/archives/<CHANNEL>/p<TS>` → basic
- `...p<TS>?thread_ts=<PARENT>&cid=<CH>` → threaded reply

Timestamp: strip `p` prefix, insert `.` before last 6 digits.

## Reference Documentation

| Reference | Content |
|-----------|---------|
| `references/api-reference.md` | Endpoint table with methods, scopes, rate tiers |
| `references/canvas-operations.md` | Size limits, quip vs new-type, auto-chunking, update patterns |
