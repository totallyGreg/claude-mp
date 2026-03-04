# Plan: Add `ofo:` Slash Commands & `omnifocus://` URL Directive

## Context

When the user pastes an `omnifocus://` URL, the system currently routes through the full omnifocus-agent, which spends ~14 tool uses and 130+ seconds re-reading skill docs before doing a simple lookup. Adding a URL directive and lightweight slash commands will make common operations instant.

## Changes

### 1. Rename existing commands from `of:` to `ofo:` prefix

Rename files and update internal references:

- `commands/of-plan.md` → `commands/ofo-plan.md` (update HTML comment inside)
- `commands/of-work.md` → `commands/ofo-work.md` (update HTML comment inside)

### 2. Create 6 new slash commands

All in `plugins/omnifocus-manager/commands/`. Each is a lightweight markdown file with frontmatter + a short instruction block that runs the appropriate script directly.

| File | Invoked as | Script call |
|---|---|---|
| `ofo-today.md` | `/ofo:today` | `manage_omnifocus.js today` |
| `ofo-inbox.md` | `/ofo:inbox` | `gtd-queries.js --action inbox-count` |
| `ofo-overdue.md` | `/ofo:overdue` | `manage_omnifocus.js overdue` |
| `ofo-info.md` | `/ofo:info <url-or-id>` | `manage_omnifocus.js info --id <parsed-id>` |
| `ofo-health.md` | `/ofo:health` | `gtd-queries.js --action system-health` |
| `ofo-search.md` | `/ofo:search <term>` | `manage_omnifocus.js search --query "<term>"` |

Each command follows the existing pattern:
```yaml
---
description: <one-liner>
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*)
---
```

The `/ofo:info` command will include URL parsing logic to extract the ID from `omnifocus:///project/<id>` or `omnifocus:///task/<id>` patterns.

### 3. Add `omnifocus://` URL directive to skill description

In `skills/omnifocus-manager/SKILL.md` frontmatter description, add trigger phrase:
```
When the user pastes an `omnifocus://` URL, parse the entity type and ID,
then run `manage_omnifocus.js info --id <id>` to look it up.
```

### 4. Add `omnifocus://` URL routing to agent

In `agents/omnifocus-agent.md` intent classification table, add a row:
```
| `omnifocus://` URL pasted | omnifocus-manager | `manage_omnifocus.js info --id <parsed-id>` |
```

And add an example block showing URL handling.

## Files Modified

1. `plugins/omnifocus-manager/commands/of-plan.md` → rename to `ofo-plan.md`
2. `plugins/omnifocus-manager/commands/of-work.md` → rename to `ofo-work.md`
3. `plugins/omnifocus-manager/agents/omnifocus-agent.md` — add URL routing row + example
4. `plugins/omnifocus-manager/skills/omnifocus-manager/SKILL.md` — add URL trigger to description

## Files Created

5. `plugins/omnifocus-manager/commands/ofo-today.md`
6. `plugins/omnifocus-manager/commands/ofo-inbox.md`
7. `plugins/omnifocus-manager/commands/ofo-overdue.md`
8. `plugins/omnifocus-manager/commands/ofo-info.md`
9. `plugins/omnifocus-manager/commands/ofo-health.md`
10. `plugins/omnifocus-manager/commands/ofo-search.md`

## Verification

1. Run each new command to confirm it produces output:
   - `/ofo:today`, `/ofo:inbox`, `/ofo:overdue`, `/ofo:health`
   - `/ofo:info omnifocus:///project/ap5cYpN4i9M`
   - `/ofo:search "End of Day"`
2. Confirm renamed commands still work: `/ofo:plan`, `/ofo:work`
3. Paste an `omnifocus://` URL without a slash command and confirm it routes to the skill directly
4. Run skillsmith evaluation: `uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py plugins/omnifocus-manager/skills/omnifocus-manager`
