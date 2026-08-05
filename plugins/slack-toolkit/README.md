# slack-toolkit

Slack Web API toolkit for Claude Code agents, built on `slack_sdk`. Two headline jobs: **pull large threads and channel history into readable, name-resolved markdown for parsing**, and **publish shareable Slack Canvases from local markdown files**. Also covers catch-up digests, channel resolution, scope verification, reactions, and full Canvas CRUD.

## Why This Exists

The official Slack MCP plugin cannot read or author Canvas content, dumps raw JSON, and has no reaction support. This toolkit is the union of readable extraction (à la slack-miner) and Canvas authoring: resolve user names, render clean markdown, verify scopes, and manage the full Canvas lifecycle — exposed as aggregate CLI commands and slash commands for human and agent use.

## Capabilities

- **Thread → readable markdown** — Pull a full thread by URL or channel+ts; user IDs resolved to names, `<url|label>` rendered as markdown links, files listed, replies nested. Markdown by default; `--json` for enriched JSON.
- **History & catch-up** — Channel history with `--since` time ranges (`Nh/Nd/Nw`/`YYYY-MM-DD`), and multi-channel `catchup` digests (pulls threads, resolves names once, skips empty channels). Supports a reusable channel-list file.
- **Cross-channel search** — `search` queries `search.messages` across every channel and DM you can access or contributed to, with modifiers (`in:#channel`, `from:@me`, `after:`/`before:`). User token + `search:read` scope.
- **Canvas publishing** — `canvas publish` turns a markdown file into a Canvas and shares it with channels/users in one command (H4+ auto-downgraded to H3).
- **Canvas CRUD** — read, create, update (append/replace, auto-chunked ~4KB), delete, rewrite (quip→new-type), channel tabs, access management, and workspace `probe`.
- **Auth & scopes** — `auth-check` verifies the token and reports missing scopes before other ops fail. The standalone `scope_manager.py` helper edits the app manifest's scopes (add/remove) with auto-backup and one-command `revert` — for when a reinstall turns out to need approval you can't get. Uses an app config token.
- **Reactions** — Add/remove emoji reactions (not available via MCP).
- **URL parsing** — Convert Slack message URLs (incl. threaded reply URLs) to channel ID + timestamp.
- **Enterprise Grid compatible** — `slack_sdk` POSTs form-encoded, as Grid requires.

## Requirements

- [`uv`](https://docs.astral.sh/uv/) — runs the CLI and auto-installs `slack_sdk` + `pip-system-certs` from the script's PEP 723 inline dependencies
- `$SLACK_USER_TOKEN` (xoxp-) — set via env var or macOS Keychain (`keychainctl`)
- Optional: `$SLACK_BOT_TOKEN` (xoxb-) for bot-scoped operations (`--bot`)

## Quick Start

```bash
# Verify token + required scopes first
uv run skills/slack-toolkit/scripts/slacker.py auth-check

# Pull a full thread as readable markdown (by URL, or channel + ts)
uv run skills/slack-toolkit/scripts/slacker.py thread "https://workspace.slack.com/archives/C0123/p1768255289788089"

# Catch up across channels over the last 7 days
uv run skills/slack-toolkit/scripts/slacker.py catchup --channels C0123 C0456 --since 7d

# Publish a Canvas from a markdown file and share it
uv run skills/slack-toolkit/scripts/slacker.py canvas publish "Team Update" --file report.md --share-channels C0123

# Resolve a channel name to IDs
uv run skills/slack-toolkit/scripts/slacker.py channels --resolve news
```

## Slash Commands

`/slack-thread` · `/slack-search` · `/slack-canvas` · `/slack-catchup` · `/slack-channels` · `/slack-auth`

## Version History

| Version | Date | Overall | Conc | Comp | Spec | Disc | Desc | Changes |
|---------|------|---------|------|------|------|------|------|---------|
| 2.1.0 | 2026-08-05 | 98 | 100 | 90 | 100 | 100 | 100 | Add `mine` — ranked `from:@me` participation per channel over a `--since` window with **no `search:read`** (thread-aware via `reply_users` pruning; resilient sweep skips unreadable channels; progress indicator); `scope_manager.py` auto-sources config tokens from the `slack` CLI login store (`~/.slack/credentials.json`); scope preflight fails loudly with the exact missing scope + fix; docs for `mine` and the `slack` CLI |
| 2.0.0 | 2026-08-03 | 98 | 100 | 90 | 100 | 100 | 100 | **Breaking:** rebuilt on slack_sdk via `uv run` (was `python3`). Add readable markdown extraction (thread/history/catchup with name resolution), cross-channel `search`, `channels`/`auth-check`, `canvas publish`, standalone `scope_manager.py` (manifest scope add/remove/revert); 6 slash commands + extraction & scope-management references |
| 1.5.1 | 2026-04-10 | 98 | 100 | 90 | 100 | 100 | 100 | Add API response trust guidance; clarify quip detection is a pre-flight heuristic; no verification read needed after ok:true |
| 1.5.0 | 2026-04-08 | 98 | 100 | 90 | 100 | 100 | 100 | Fix canvas read (remove broken sections.lookup path, unify on url_private); add canvas sections lookup |
| 1.4.0 | 2026-04-08 | 98 | 100 | 90 | 100 | 100 | 100 | Add canvas delete, channel-create, access set/delete commands; comprehensive API reference |
| 1.3.0 | 2026-04-08 | 98 | 100 | 90 | 100 | 100 | 100 | Remove 3KB create limit (API handles 20KB+); add H4+ heading downgrade pre-flight |
| 1.2.0 | 2026-04-06 | 98 | 100 | 90 | 100 | 100 | 100 | Add automatic Canvas API availability test before creation; add negative trigger clause |
| 1.1.0 | 2026-03-26 | 98 | 100 | 90 | 100 | 100 | 100 | Add --append-file/--content-file to canvas update, auto-chunking for large content, canvas-operations reference |
| 1.0.0 | 2026-03-26 | 95 | 100 | 90 | 100 | 85 | 100 | Initial release: canvas CRUD, reactions, threads, history, URL parsing |

## Skill: slack-toolkit

### Current Metrics

**Score: 98/100** (Excellent) — 2026-08-05 (verified, receipt hash 08164cd198ed)

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 2.1.0 | 2026-08-05 | - | Add `mine` (ranked `from:@me` participation, no search:read, thread-aware via reply_users pruning); scope_manager sources config tokens from slack CLI; scope preflight; slack CLI + mine docs | 100 | 90 | 100 | 100 | 100 | 98 |
| 2.0.0 | 2026-08-03 | - | Rebuild on slack_sdk (uv); readable extraction (thread/history/catchup), cross-channel search, canvas publish, 6 slash commands, extraction reference | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.5.0 | 2026-04-08 | - | Fix canvas read (url_private-first, remove broken sections.lookup); add sections lookup command | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.4.0 | 2026-04-08 | - | Add canvas delete, channel-create, access set/delete; comprehensive API reference | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.3.0 | 2026-04-08 | - | Remove 3KB create limit; add H4+ heading downgrade pre-flight | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.2.0 | 2026-04-06 | - | slack-toolkit v1.2.0 | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.1.0 | 2026-03-26 | - | Add --append-file, auto-chunking, canvas-operations ref | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.0.0 | 2026-03-26 | - | Initial release | 100 | 90 | 100 | 85 | 100 | 95 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)
