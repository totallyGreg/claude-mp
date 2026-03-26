# slack-toolkit

Slack Web API access via Python CLI for Claude Code agents. Fills gaps in the official Slack MCP plugin and provides a full fallback when MCP is unavailable.

## Capabilities

- **Canvas CRUD**: Read, create, and update Slack Canvases (MCP only supports create)
- **Reactions**: Add and remove emoji reactions (MCP cannot do this)
- **Threads**: Retrieve full threaded conversations with pagination
- **Channel History**: Read channel message history with pagination
- **URL Parsing**: Convert Slack message URLs to channel ID + timestamp

## Requirements

- Python 3.8+
- `$SLACK_USER_TOKEN` (xoxp-) — set via env var or macOS Keychain
- Optional: `$SLACK_BOT_TOKEN` (xoxb-) for bot operations

## Quick Start

```bash
# Read a canvas
python3 skills/slack-toolkit/scripts/slacker.py canvas read F0ABC123DEF

# Add a reaction
python3 skills/slack-toolkit/scripts/slacker.py react C0123 1234567890.123456 thumbsup

# Get a thread
python3 skills/slack-toolkit/scripts/slacker.py thread C0123 1234567890.123456
```

## Version History

| Version | Date | Overall | Conc | Comp | Spec | Disc | Desc | Changes |
|---------|------|---------|------|------|------|------|------|---------|
| 1.1.0 | 2026-03-26 | 98 | 100 | 90 | 100 | 100 | 100 | Add --append-file/--content-file to canvas update, auto-chunking for large content, canvas-operations reference |
| 1.0.0 | 2026-03-26 | 95 | 100 | 90 | 100 | 85 | 100 | Initial release: canvas CRUD, reactions, threads, history, URL parsing |

## Skill: slack-toolkit

### Current Metrics

**Score: 98/100** (Excellent) — 2026-03-26

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.1.0 | 2026-03-26 | - | Add --append-file, auto-chunking, canvas-operations ref | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.0.0 | 2026-03-26 | - | Initial release | 100 | 90 | 100 | 85 | 100 | 95 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)
