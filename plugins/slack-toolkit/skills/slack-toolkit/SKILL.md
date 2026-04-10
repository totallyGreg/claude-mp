---
name: slack-toolkit
metadata:
  version: "1.5.1"
compatibility: Requires python3 for slacker.py CLI execution
license: MIT
description: >-
  Use this skill when the Slack MCP server is not connected, when you need
  Canvas read/update operations, when you need to add/remove reactions, or
  when direct Slack API access is explicitly requested. Triggers on "read
  slack canvas", "update slack canvas", "create slack canvas", "rewrite
  slack canvas", "add slack reaction", "remove slack reaction", "get slack
  thread", "slack channel history", "parse slack url", "slack without mcp",
  "slack api curl". Do NOT use for channel/message operations when the Slack
  MCP server is available — use the official MCP plugin instead.
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

The `canvas create` command automatically tests Canvas API availability before creating canvases. Run `canvas probe` to detect your workspace type. On quip workspaces, updating content requires creating a new canvas with the full content.

## CLI Reference

All commands: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/slack-toolkit/scripts/slacker.py <command> [args]`

### Canvas Operations (MCP gaps)

```bash
# Read canvas content via url_private (reliable for quip canvases; new-type support varies by workspace)
# There is no official canvases.read API — content is fetched via files.info → url_private.
# On failure, outputs JSON metadata (canvas_id, title, filetype, permalink) and exits non-zero.
slacker.py canvas read <canvas_id>

# Create standalone canvas
slacker.py canvas create <title> --content "# Markdown content"
slacker.py canvas create <title> --content-file /path/to/file.md

# Create channel-pinned canvas tab (one per channel; use read to find existing)
slacker.py canvas channel-create <channel_id> --title "Title" --content-file /path/to/file.md

# Update canvas — append from file (recommended for code blocks / large content)
slacker.py canvas update <canvas_id> --append-file /path/to/content.md

# Update canvas — replace a section (requires section_id from read)
slacker.py canvas update <canvas_id> --replace <section_id> --content-file /path/to/content.md

# Find section IDs for targeted in-place edits (atomic edit workflow)
slacker.py canvas sections lookup <canvas_id> --section-types h2 --contains-text "Status"
# → {"sections": [{"id": "temp:C:abc123..."}]}

# Then replace that section atomically (no canvas recreation needed)
slacker.py canvas update <canvas_id> --replace temp:C:abc123... --content-file new-status.md

# Delete a canvas permanently (irreversible)
slacker.py canvas delete <canvas_id>

# Manage canvas access
slacker.py canvas access set <canvas_id> read|write|owner --channel-ids C1 C2
slacker.py canvas access set <canvas_id> write --user-ids U1 U2
slacker.py canvas access delete <canvas_id> --channel-ids C1
slacker.py canvas access delete <canvas_id> --user-ids U1

# Rewrite quip canvas as new-type (creates new canvas, outputs both IDs)
slacker.py canvas rewrite <canvas_id>

# Detect workspace canvas type (quip vs new-type)
slacker.py canvas probe
```

Canvas content uses markdown. `canvas create` and `canvas channel-create` send full content in one call (large payloads supported); H4+ headings are auto-downgraded to H3 with a warning. `canvas update --append-file` auto-chunks appends into ~4KB operations. On quip workspaces, create still works but append/replace does not. `--channel-ids` and `--user-ids` are mutually exclusive for access commands. See `references/canvas-operations.md` and `references/api-reference.md` for details.

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
- **stderr**: Human-readable errors and pre-flight warnings (speculative — do not treat as failures)
- **Exit codes**: 0=success, 1=usage, 2=auth, 3=API error, 4=rate limited

**API response trust:** `{"ok": true}` is authoritative — no verification read needed. Pre-flight warnings on stderr (e.g., quip detection) are heuristics emitted *before* the call — if the call returns `ok: true`, the operation succeeded regardless.

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
