---
name: slack-toolkit
metadata:
  version: "2.1.0"
compatibility: Requires uv for Python script execution (slack_sdk auto-installed via PEP 723 inline dependencies)
license: MIT
description: >-
  This skill should be used when working directly with the Slack Web API to
  extract conversations or author Canvases. Use it to "convert slack thread to
  markdown", "read slack channel history", "build slack catchup digest",
  "create slack canvas", "update slack canvas", "generate slack canvas from
  markdown", "check slack scopes", "parse slack url", or "add slack reaction".
  It resolves user names, renders readable markdown, and provides full Canvas
  CRUD. Do NOT use for quick single-message channel posting when the Slack MCP
  server is available — prefer MCP for those; use this for large-thread
  extraction, Canvas authoring, reactions, and scope verification.
---

# Slack Toolkit

Slack Web API CLI built on `slack_sdk`. Two headline jobs: **pull large threads/history into readable markdown for parsing**, and **publish readable Canvases from local markdown files** to share with a team. Also covers catch-up digests, channel resolution, scope verification, reactions, and full Canvas CRUD.

> **Positioning:** Prefer the official Slack MCP server for quick single-message channel operations. Use this toolkit for large-thread extraction (name-resolved markdown), Canvas read/authoring (MCP cannot do Canvas), reactions, and scope checks.

## Configuration

| Variable | Source | Required |
|----------|--------|----------|
| `$SLACK_USER_TOKEN` | Env var or `keychainctl get SLACK_USER_TOKEN` | Yes |
| `$SLACK_BOT_TOKEN` | Env var or `keychainctl get SLACK_BOT_TOKEN` | Optional (`--bot`) |

Token resolution: env var first, `keychainctl` fallback (macOS). Prefix-validated (`xoxp-`/`xoxb-`). Run `auth-check` to verify scopes before other operations.

## Invocation

All commands run via `uv` (auto-installs `slack_sdk` + `pip-system-certs` from the PEP 723 block):

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/slack-toolkit/scripts/slacker.py <command> [args]
```

Slash commands wrap the common flows: `/slack-thread`, `/slack-search`, `/slack-canvas`, `/slack-catchup`, `/slack-channels`, `/slack-auth`. `slack_sdk` POSTs form-encoded, so Enterprise Grid works with no extra handling.

## Reading & Extraction

Thread/history/catchup default to **readable markdown** (user IDs resolved to names, `<url|label>` → `[label](url)`, files listed, thread replies indented). Add `--json` for **enriched** JSON (each message gets `author_name`; threads nested under `_replies`). See `references/extraction.md` for workflows, time-range formats, and the channel-list file format.

```bash
# Full thread by URL (or channel ID + parent ts) → markdown
slacker.py thread "https://workspace.slack.com/archives/C0123/p1768255289788089"
slacker.py thread C0123 1768255289.788089 --limit 1000 --json

# Channel history over a time range (Nh / Nd / Nw / YYYY-MM-DD)
slacker.py history C0123 --since 7d
slacker.py history C0123 --limit 200 --json

# Multi-channel catch-up digest (pulls threads, resolves names once)
slacker.py catchup --channels C0123 C0456 --since 3d
slacker.py catchup --channels-file channels.md --since 2026-03-01

# Search across ALL channels/DMs you can access or contributed to (needs search:read)
slacker.py search "prisma airs incident"
slacker.py search "from:@me in:#team-eng after:2026-03-01" --count 200 --json

# Rank YOUR OWN participation per channel over a window — a from:@me view that needs
# NO search:read (uses channels:history). Reusable: just vary --since.
slacker.py mine --since 6w                    # ranked table, most-active channels first
slacker.py mine --since 2026-01-01 --threads --json   # reply-inclusive, structured

# List or resolve your channels
slacker.py channels                 # markdown table (ID · name · topic)
slacker.py channels --resolve news  # {id, name} matches for /slack-thread etc.

# Verify token + required scopes (run first when commands fail)
slacker.py auth-check
```

## Canvas Authoring

Slack has two canvas backends. Type is set at the **workspace level** — some (Enterprise Grid) route all creation through legacy **Quip**, even via `canvases.create`:

- **Quip** (`filetype: "quip"`): read works (HTML→markdown); `canvases.edit` (append/replace) does not. To update, recreate with full content.
- **New Canvas API**: full CRUD; large appends auto-chunk (~4KB/op).

Run `canvas probe` to detect your workspace type. See `references/canvas-operations.md` and `references/api-reference.md`.

```bash
# Publish a canvas from a markdown file, optionally sharing it (headline flow)
slacker.py canvas publish "Team Update" --file report.md \
  --share-channels C0123 --share-users U0456 --access read
slacker.py canvas publish "Runbook" --file runbook.md --channel-tab C0123

# Primitives
slacker.py canvas read <canvas_id>                     # → markdown
slacker.py canvas create "Title" --content-file doc.md # single call; H4+ → H3
slacker.py canvas update <canvas_id> --append-file more.md   # auto-chunked
slacker.py canvas sections lookup <canvas_id> --section-types h2 --contains-text "Status"
slacker.py canvas update <canvas_id> --replace <section_id> --content-file new.md
slacker.py canvas channel-create <channel_id> --title "Tab" --content-file doc.md
slacker.py canvas access set <canvas_id> write --channel-ids C1  # or --user-ids U1
slacker.py canvas access delete <canvas_id> --channel-ids C1
slacker.py canvas probe            # detect quip vs new-type
slacker.py canvas rewrite <canvas_id>   # quip → new-type (creates new canvas)
slacker.py canvas delete <canvas_id>    # irreversible
```

`canvas publish` and `canvas create` auto-downgrade H4+ headings to H3 (Slack rejects H4+). `--share-channels` and `--share-users` may be combined (two access calls); `--channel-ids`/`--user-ids` are mutually exclusive within a single `access` call.

## Reactions

```bash
slacker.py react <channel> <timestamp> <emoji_name>     # name without colons
slacker.py unreact <channel> <timestamp> <emoji_name>
```

## URL Parsing

```bash
slacker.py parse-url "https://workspace.slack.com/archives/C0123/p1768255289788089"
```

Strips the `p` prefix and inserts `.` before the last 6 digits. Threaded reply URLs (`?thread_ts=…&cid=…`) resolve to the parent thread.

## Output Contract

- **stdout**: markdown (default for reads/canvas read) or JSON (writes, `--json`, metadata).
- **stderr**: human-readable errors + pre-flight warnings (heuristic — not failures).
- **Exit codes**: 0=success, 1=usage, 2=auth, 3=API error, 4=rate limited.

**Response trust:** `slack_sdk` raises on `ok:false`, so any returned response succeeded — `{"canvas_id": …}`/`{"ok": true}` is authoritative; no verification read needed. Pre-flight warnings (e.g. quip detection) fire *before* the call; if it returns success, it worked.

## Required Scopes

`auth-check` verifies the full set: `channels:history/read`, `groups:history/read`, `im:history/read`, `mpim:history/read`, `users:read`, `search:read` (cross-channel `search`, user token only), `files:read`, `canvases:read/write`, `reactions:write`. Missing scopes are reported (non-fatal) so you know which commands will fail.

**Scope preflight (per operation).** Scope-sensitive commands check their required scope *before* the API call, so a missing scope fails loudly with the exact scope name + a fix — not a bare `missing_scope` mid-run. If a call still reaches Slack and returns `missing_scope`, the error handler surfaces Slack's own `needed` scope plus the same fix guidance. Per-operation scopes:

| Operation | Required scope(s) |
|-----------|-------------------|
| `search` | `search:read` (**user token only** — `--bot` is rejected) |
| `mine` | `channels:history` (+ `groups:history` for private channels) — reconstructs `from:@me` with **no `search:read`**; skips channels it can't read |
| `history` / `thread` / `catchup` | `channels:history` (+ `groups:history` / `im:history` / `mpim:history` for private, DM, group-DM conversations) |
| `channels` | `channels:read` (+ `groups:read` / `im:read` / `mpim:read` to list those types) |
| `react` / `unreact` | `reactions:write` |
| `canvas *` | `canvases:read` (read/lookup), `canvases:write` (create/edit/delete/access), `files:read` (type detection) |

When `search:read` is unavailable (e.g. Enterprise Grid blocks it behind admin approval), use `mine` for a `from:@me` participation view — it needs only `channels:history`, which you already have.

To change the app's scopes when some are missing, the standalone `scripts/scope_manager.py` helper edits the app manifest (with auto-backup and one-command `revert`) — it needs an app **config token** (`xoxe.…`), not the user token, and a manual browser reinstall still applies. The config token is read from `$SLACK_CONFIG_TOKEN`, then keychain, then the **`slack` platform CLI** login store (`~/.slack/credentials.json`) — so after `slack login` the helper works with no manual token export. See `references/scope-management.md`.

## Reference Documentation

| Reference | Content |
|-----------|---------|
| `references/extraction.md` | thread/history/catchup workflows, `--since` formats, user-cache, channel-list file format |
| `references/api-reference.md` | endpoint table with methods, scopes, rate tiers |
| `references/canvas-operations.md` | quip vs new-type, size limits, auto-chunking, publish/update patterns |
| `references/scope-management.md` | `scope_manager.py` helper — config tokens, add/remove/revert scopes, reinstall loop |
