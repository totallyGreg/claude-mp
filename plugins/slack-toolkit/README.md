# slack-toolkit

Slack Web API toolkit for Claude Code agents. Provides direct Slack API access via a zero-dependency Python CLI, filling capability gaps in the official Slack MCP plugin and serving as a complete fallback when MCP is unavailable.

## Why This Exists

The official Slack MCP plugin cannot read or update Canvas content, and has no reaction support. This toolkit bridges those gaps while also providing paginated thread/history retrieval and Slack URL parsing — all through a single CLI with no external dependencies.

## Capabilities

- **Canvas CRUD** — Full canvas lifecycle: read, create, update (append/replace), delete, and rewrite (quip→new-type). `canvas create` sends full content in a single API call (20KB+ supported); H4+ headings are auto-downgraded to H3. `canvas update --append-file` auto-chunks large appends into ~4KB operations.
- **Channel Canvas** — Create channel-pinned canvas tabs via `canvas channel-create`. Handles the one-per-channel constraint; H4+ heading downgrade applies here too.
- **Canvas Access Management** — Grant or revoke canvas access for users or channels via `canvas access set/delete`. Supports `read`, `write`, and `owner` levels with mutual-exclusivity enforcement between `--channel-ids` and `--user-ids`.
- **Canvas Probe** — Detects whether a workspace produces quip or new-type canvases, so agents can choose the right strategy before creating content.
- **Reactions** — Add and remove emoji reactions on any message (not available via MCP).
- **Threads** — Retrieve full threaded conversations with cursor-based pagination (up to 1000 messages).
- **Channel History** — Read channel message history with pagination.
- **URL Parsing** — Convert Slack message URLs (including threaded reply URLs) to channel ID + timestamp components.
- **Enterprise Grid Compatible** — All API calls use POST with form-encoded bodies, which is required for Slack Enterprise Grid workspaces.

## Requirements

- Python 3.8+ (stdlib only — no pip dependencies)
- `$SLACK_USER_TOKEN` (xoxp-) — set via env var or macOS Keychain (`keychainctl`)
- Optional: `$SLACK_BOT_TOKEN` (xoxb-) for bot-scoped operations

## Quick Start

```bash
# Read a canvas (auto-detects quip vs new-type, outputs markdown)
python3 skills/slack-toolkit/scripts/slacker.py canvas read F0ABC123DEF

# Create a canvas from a file (single API call, H4+ headings auto-downgraded to H3)
python3 skills/slack-toolkit/scripts/slacker.py canvas create "My Doc" --content-file report.md

# Add a reaction
python3 skills/slack-toolkit/scripts/slacker.py react C0123 1234567890.123456 thumbsup

# Get a full thread
python3 skills/slack-toolkit/scripts/slacker.py thread C0123 1234567890.123456

# Parse a Slack URL
python3 skills/slack-toolkit/scripts/slacker.py parse-url "https://workspace.slack.com/archives/C0123/p1768255289788089"
```

## Version History

| Version | Date | Overall | Conc | Comp | Spec | Disc | Desc | Changes |
|---------|------|---------|------|------|------|------|------|---------|
| 1.5.0 | 2026-04-08 | 98 | 100 | 90 | 100 | 100 | 100 | Fix canvas read (remove broken sections.lookup path, unify on url_private); add canvas sections lookup |
| 1.4.0 | 2026-04-08 | 98 | 100 | 90 | 100 | 100 | 100 | Add canvas delete, channel-create, access set/delete commands; comprehensive API reference |
| 1.3.0 | 2026-04-08 | 98 | 100 | 90 | 100 | 100 | 100 | Remove 3KB create limit (API handles 20KB+); add H4+ heading downgrade pre-flight |
| 1.2.0 | 2026-04-06 | 98 | 100 | 90 | 100 | 100 | 100 | Add automatic Canvas API availability test before creation; add negative trigger clause |
| 1.1.0 | 2026-03-26 | 98 | 100 | 90 | 100 | 100 | 100 | Add --append-file/--content-file to canvas update, auto-chunking for large content, canvas-operations reference |
| 1.0.0 | 2026-03-26 | 95 | 100 | 90 | 100 | 85 | 100 | Initial release: canvas CRUD, reactions, threads, history, URL parsing |

## Skill: slack-toolkit

### Current Metrics

**Score: 98/100** (Excellent) — 2026-04-08

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.5.0 | 2026-04-08 | - | Fix canvas read (url_private-first, remove broken sections.lookup); add sections lookup command | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.4.0 | 2026-04-08 | - | Add canvas delete, channel-create, access set/delete; comprehensive API reference | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.3.0 | 2026-04-08 | - | Remove 3KB create limit; add H4+ heading downgrade pre-flight | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.2.0 | 2026-04-06 | - | slack-toolkit v1.2.0 | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.1.0 | 2026-03-26 | - | Add --append-file, auto-chunking, canvas-operations ref | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.0.0 | 2026-03-26 | - | Initial release | 100 | 90 | 100 | 85 | 100 | 95 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)
