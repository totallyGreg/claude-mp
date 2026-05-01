---
name: omnifocus-core
description: |
  This skill should be used when querying OmniFocus data, managing tasks, running GTD diagnostics, or configuring perspectives. Triggers when user asks "show tasks", "overdue items", "check inbox", "stalled projects", "waiting for list", "someday maybe", "GTD health check", "AI Agent tasks", "publish plan to OmniFocus", "set up perspectives", "perspective inventory", "configure perspective", "quick stats", or "missing perspectives". Also triggers when the user pastes an `omnifocus://` URL — parse the entity type and ID from the URL, then use `/ofo:info <url>` to look it up directly.

  Do NOT trigger for: "create OmniFocus plugin" (use omnifocus-generator skill), "analyze my system" or "discover my patterns" (use attache-analyst skill), pure GTD methodology questions (use gtd-coach skill).
license: MIT
metadata:
  version: 11.0.0
  author: totally-tools
compatibility:
  platforms: [macos]
  requires:
    - OmniFocus 3 or 4
    - macOS with automation permissions
---

# OmniFocus Core

Stateless data access layer for OmniFocus — task CRUD, queries, perspectives, and reporting.

## Skill Architecture

| Skill | Focus | Handoff |
|-------|-------|---------|
| **omnifocus-core** (this) | Task CRUD, queries, perspectives | — |
| **omnifocus-generator** | OmniFocus plugin/script generation | "Create OmniFocus plugin" → defer |
| **attache-analyst** | System learning, AI coaching, metrics | "Analyze my system" → defer |
| **gtd-coach** | Pure GTD methodology coaching | "What makes a good next action?" → defer |

## ofo CLI (Preferred for All Operations)

The `ofo` CLI executes Omni Automation scripts directly inside OmniFocus via script URLs. **Use ofo for all task CRUD and queries.**

```bash
scripts/ofo info <id-or-omnifocus-url>       # Task/project details
scripts/ofo complete <id-or-omnifocus-url>   # Mark task complete
scripts/ofo drop <id-or-omnifocus-url>       # Drop single occurrence (recurrence continues)
scripts/ofo drop <id-or-omnifocus-url> --all # Drop all occurrences (stops repeating)
scripts/ofo health                           # System health: inbox, overdue, flagged (single call)
scripts/ofo create --name "Task" --project "Work" --due 2026-12-31
scripts/ofo update <id> --name "New name" --flagged
scripts/ofo update <id> --note "text"                # Replace task note entirely
scripts/ofo update <id> --note-append "text"         # Append text to existing note
scripts/ofo search "meeting"                 # Search by name/note
scripts/ofo list inbox                       # List inbox tasks
scripts/ofo list today                       # Flagged + due today + planned today
scripts/ofo list overdue                     # Past due date
scripts/ofo list flagged                     # All flagged active tasks
scripts/ofo list due-soon [N]               # Tasks due within N days (default 7)
scripts/ofo tag <id> --add "Tag" --remove "Other"  # Granular tag manipulation
scripts/ofo tag <id> --capture question      # Capture pipeline shortcut
scripts/ofo tags                             # Full tag hierarchy as JSON
scripts/ofo perspective-list                 # All perspective names
scripts/ofo perspective-rules                # All custom perspectives with resolved filter rules
scripts/ofo perspective-rules "Name"         # Single perspective filter rules (IDs → named links)
scripts/ofo perspective-configure --name "View" --rules '[...]'  # Set perspective filter rules
scripts/ofo completed-today                  # Today's completions categorized by tag (JSON)
scripts/ofo completed-today --markdown       # Same, formatted for Obsidian append
scripts/ofo dump                             # Snapshot JSON: tasks (500 cap), projects, perspectives
scripts/ofo stats                            # Counts: inbox/flagged/overdue/projects/tasks/reviewOverdue/plannedToday/withEstimate
```

**Prerequisites:** OmniFocus running + external scripts enabled. First command triggers a one-time approval dialog.

## JXA Diagnostics (Advanced Queries)

**GTD diagnostics** via `scripts/gtd-queries.js` — for queries not yet covered by ofo:
```bash
osascript -l JavaScript scripts/gtd-queries.js --action system-health
osascript -l JavaScript scripts/gtd-queries.js --action stalled-projects
osascript -l JavaScript scripts/gtd-queries.js --action waiting-for
osascript -l JavaScript scripts/gtd-queries.js --action someday-maybe
osascript -l JavaScript scripts/gtd-queries.js --action recently-completed --days 7
osascript -l JavaScript scripts/gtd-queries.js --action neglected-projects --threshold 30
osascript -l JavaScript scripts/gtd-queries.js --action ai-agent-tasks
osascript -l JavaScript scripts/gtd-queries.js --action repeating-tasks --days 90
osascript -l JavaScript scripts/gtd-queries.js --action analyze-projects --threshold 30
osascript -l JavaScript scripts/gtd-queries.js --action folder-structure
```

**Legacy:** `scripts/manage_omnifocus.js` retained only for `bulk-create` (structured projects with action groups). All other commands covered by ofo CLI.

## Perspectives

**Principle: Perspectives over scripts.** Prefer codifying perspectives as the query engine over creating new plugin actions.

```bash
scripts/ofo perspective-list                        # List all perspective names
scripts/ofo perspective "Completed Today"           # Query perspective contents
scripts/ofo perspective-rules                       # All custom perspectives + archivedFilterRules
scripts/ofo perspective-rules "Dashboard"           # Single perspective rules
scripts/ofo perspective-configure --name "View" --rules '[...]'  # Write filter rules
```

**Perspective structure:** Set via OmniFocus UI (Perspectives → Edit → Structure).
- **Flexible** — flat list; best for "what's next" scanning across projects
- **Organized** — grouped + sorted; best for categorical review

Perspectives must be created manually in OmniFocus Pro — the API has no constructor.

See `references/perspective_templates.md` for 8 canonical GTD perspective JSON configs.
See `references/perspective_creation.md` for the guided configuration workflow.

## Script Conventions

- **Prefer ofo CLI** for task CRUD: `scripts/ofo <command>`
- **Single-action pattern**: One call = one pasteboard round-trip = reliable results
- **Commands use `${CLAUDE_PLUGIN_ROOT}`**: `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-core/scripts/`
- **Smoke test before version bump**: `bash scripts/test-queries.sh`

## Execution Hierarchy

1. **ofo CLI** (preferred): `scripts/ofo <command>`
2. **gtd-queries.js** (JXA diagnostics only): `osascript -l JavaScript scripts/gtd-queries.js --action <action>`
3. **manage_omnifocus.js** (legacy — bulk-create only): `osascript -l JavaScript scripts/manage_omnifocus.js bulk-create --json-file <path>`

## Reference Documentation

- **[Official OmniFocus API](https://omni-automation.com/omnifocus/OF-API.html)** - Canonical API reference
- `references/api_reference.md` - Local quick lookup tables
- `references/jxa_guide.md` - Command-line automation
- `references/gtd_guide.md` - GTD-to-OmniFocus mapping
- `references/perspective_creation.md` - Guided configuration (v4.2+)
- `references/perspective_templates.md` - 8 canonical GTD perspective JSON configs
- `references/omnifocus_url_scheme.md` - Quick capture and linking
- `references/omnifocus_api.md` - Full API specification
- `references/omni_automation_api_mapping.md` - JXA vs script URL API differences
- `references/database_schema.md`, `references/workflows.md`
- `references/troubleshooting.md` - Permission issues, common errors, debugging
