---
name: omnifocus-manager
description: |
  This skill should be used when working with OmniFocus data, running GTD diagnostics, configuring perspectives, or generating OmniFocus plugins. Triggers when user asks "show tasks", "overdue items", "check inbox", "stalled projects", "waiting for list", "someday maybe", "GTD health check", "create a plugin", "analyze OmniFocus", "AI Agent tasks", "publish plan to OmniFocus", "set up perspectives", "perspective inventory", "configure perspective", or "missing perspectives". Also triggers when the user pastes an `omnifocus://` URL — parse the entity type and ID from the URL, then use `/ofo:info <url>` to look it up directly. For pure GTD methodology coaching, use the gtd-coach skill instead.

  WORKFLOW: 1) CLASSIFY query vs plugin 2) SELECT format (solitary/solitary-fm/bundle/solitary-library) 3) COMPOSE from libraries 4) GENERATE via `node scripts/generate_plugin.js` - NEVER Write/Edit tools 5) VALIDATE via `bash scripts/validate-plugin.sh` 6) TEST in OmniFocus.
license: MIT
metadata:
  version: 9.4.0
  author: totally-tools
compatibility:
  platforms: [macos]
  requires:
    - OmniFocus 3 or 4
    - Node.js 18+ (for TypeScript plugin generation)
    - macOS with automation permissions
---

# OmniFocus Manager

## ⚡ CRITICAL: Plugin Generation Workflow

**If user requests "create plugin" or "make plugin", follow these EXACT steps:**

### STEP 1: CLASSIFY
```
Keywords in request → Classification:
- "create plugin", "make plugin", "generate plugin" → PLUGIN GENERATION (continue to step 2)
- "build JXA script", "write a script" → JXA COMPOSITION (compose from taskQuery.js/taskMutation.js, validate with validate-jxa-patterns.js)
- "automate this", "recurring task" → CHANNEL SELECTION (see references/channel_selection.md)
- "improve script", "fix script" → SCRIPT MODIFICATION (read existing, modify, validate)
- "show me", "what tasks", "analyze" → QUERY/EXECUTION (use ofo CLI or gtd-queries.js, STOP)
```

### STEP 2: SELECT FORMAT
```
- Single action, no AI     → --format solitary
- Single action, with AI   → --format solitary-fm
- Multiple actions         → --format bundle --template <name>
- Library for reuse        → --format solitary-library
```

### STEP 3: GENERATE (TypeScript validation automatic)
```bash
node scripts/generate_plugin.js --format <FORMAT> --name "<NAME>"
```
**🚫 RED FLAG:** If about to use Write or Edit tool for .js/.omnijs files → STOP, use generator instead

### STEP 4: VALIDATE (Always run)
```bash
bash scripts/validate-plugin.sh <generated-plugin-path>
```

### STEP 4.5: BUMP VERSION
Bump the version in the `.omnifocusjs` manifest — OmniFocus won't reload the plugin without a version change.

### STEP 5: REPORT
```
✅ Plugin generated: <path>
✅ Validation: PASSED → Ready for installation
open <path>   # OmniFocus prompts for install location and reloads automatically
```

See `references/code_generation_validation.md` for TypeScript validation details and anti-pattern checklist.

---

## Four-Pillar Architecture

| Pillar | Capability | Owner |
|--------|-----------|-------|
| **1. Query** | JXA/Omni Automation live database queries | omnifocus-manager |
| **2. Perspectives** | Guided perspective configuration via `archivedFilterRules` (v4.2+) | omnifocus-manager |
| **3. GTD Coaching** | Pure methodology coaching | **gtd-coach** skill |
| **4. Plugins + FM** | Plugin generation, Apple Intelligence, Attache plugin | omnifocus-manager |

See `references/gtd_guide.md` for GTD-to-OmniFocus mapping.
See `references/channel_selection.md` for Mac vs iOS routing.

---

## Quick Decision Tree

### 0. ofo CLI (Preferred for Core CRUD)

The `ofo` CLI executes Omni Automation scripts directly inside OmniFocus via script URLs. It avoids JXA permission issues and provides clean ergonomics. **Use ofo for all task CRUD and queries when possible.**

```bash
scripts/ofo info <id-or-omnifocus-url>       # Task/project details
scripts/ofo complete <id-or-omnifocus-url>   # Mark task complete
scripts/ofo create --name "Task" --project "Work" --due 2026-12-31
scripts/ofo update <id> --name "New name" --flagged
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

### 1. Query OmniFocus Data (JXA — for advanced queries not covered by ofo)

**GTD diagnostics** via `scripts/gtd-queries.js`:
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

**Legacy task/project commands** via `scripts/manage_omnifocus.js` (prefer ofo CLI — manage_omnifocus.js retained only for `bulk-create` which creates structured projects with action groups):
`bulk-create`. See `references/jxa_guide.md` for usage. All other commands now covered by ofo CLI.

### 2. Manage Perspectives

**Principle: Perspectives over scripts.** Prefer codifying perspectives as the query engine over creating new plugin actions. Use `ofo perspective` to read and `ofo perspective-configure` to write filter rules on existing perspectives. The CLI handles post-processing (filtering, categorization, formatting).

```bash
# ofo CLI (preferred)
scripts/ofo perspective-list                        # List all perspective names (built-in + custom)
scripts/ofo perspective "Completed Today"           # Query perspective contents (tasks matching rules)
scripts/ofo perspective-rules                       # All custom perspectives + archivedFilterRules (folder/tag IDs resolved to named links)
scripts/ofo perspective-rules "Dashboard"           # Single perspective rules
scripts/ofo perspective-configure --name "View" --rules '[...]'   # Write filter rules
scripts/ofo perspective-configure --name "My View" --aggregation any

# Omni Automation URL scheme (when ofo unavailable)
# Perspective.all → all perspectives (built-in + custom); Perspective.Custom.all → custom only
# Returns: array of perspective objects with .name, .archivedFilterRules, .id.primaryKey
# Use Folder.byIdentifier(id) and Tag.byIdentifier(id) to resolve IDs in filter rules

# JXA (plain osascript — limited perspective support)
osascript -l JavaScript scripts/gtd-queries.js --action perspective-inventory
# ⚠️ perspective-inventory output is the authoritative name list — stop after receiving it, do not fall back further
```

**Perspective structure (Flexible vs Organized):** Set via OmniFocus UI (Perspectives → Edit → Structure). Not yet exposed in the `archivedFilterRules` API.
- **Flexible** — flat list; best for "what's next" scanning across many projects (e.g. Dashboard)
- **Organized** — grouped + sorted view; best for categorical review (e.g. Money Check grouped by Project)

Note: Perspectives must be created manually in OmniFocus Pro — the API has no constructor. Filter rules use tag/folder IDs, not names — use `ofo perspective-rules` to read with resolved links.

See `references/perspective_templates.md` for 8 canonical GTD perspective JSON configs.
See `references/perspective_creation.md` for the guided configuration workflow.

### 3. Create Plugins

**→ See ⚡ CRITICAL workflow at top of this document**

```bash
node scripts/generate_plugin.js --format <solitary|solitary-fm|bundle> --name "Plugin Name"
bash scripts/validate-plugin.sh <generated-plugin-path>
```

See `references/omni_automation_guide.md` for plugin development details.

### 4. GTD Coaching

Use the **gtd-coach** skill for pure methodology coaching.
See `references/gtd_guide.md` for GTD-to-OmniFocus mapping.

### 5. AI Task Analysis (Attache)

Install `assets/Attache.omnifocusjs` (OmniFocus 4.8+, macOS 26+, Apple Silicon).
Attache provides 9 on-device AI actions: daily/weekly GTD reviews, project analysis,
system discovery with persistent memory, and completed task summaries.

For quick daily review, use Attache in OmniFocus; for deep system analysis, use Claude Code.

Attache consolidates and replaces the legacy AITaskAnalyzer, CompletedTasksSummary, Overview, and TodaysTasks plugins (removed in v9.4.0).

**Post-deploy:** After installing or updating Attache, refresh the System Map so coaching sessions use the latest fields:
```bash
open assets/Attache.omnifocusjs                    # install/update plugin
# Restart OmniFocus to reload plugin libraries (install dialog updates files but libraries stay cached)
osascript -e 'tell application "OmniFocus" to quit' && sleep 3 && open -a OmniFocus
sleep 8                                            # wait for OmniFocus to start and load plugins
scripts/ofo search "Attache System Map"            # get task ID
# Then trigger discovery via omnijs-run:
SCRIPT='var p=PlugIn.find("com.totallytools.omnifocus.attache");var lib=p.library("systemDiscovery");var map=lib.discoverSystem({depth:"full"});var t=flattenedTasks.filter(function(t){return t.name==="Attache System Map"});if(t.length>0){t[0].note=JSON.stringify(map);Pasteboard.general.string="System Map updated v"+map.attacheVersion}else{Pasteboard.general.string="Task not found"}'
open "omnifocus://localhost/omnijs-run?script=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.stdin.read().strip()))" <<< "$SCRIPT")"
```

See `references/foundation_models_integration.md` for Foundation Models API details.

---

## Plugin Install (ofo-core)

`npm run deploy` runs `open build/ofo-core.omnifocusjs` — OmniFocus prompts for install location and reloads automatically. No hardcoded paths, no stale-copy risk.

---

## Script Conventions

- **Prefer ofo CLI** for task CRUD: `scripts/ofo <command>` (uses Omni Automation script URLs, no CWD dependency)
- **CWD must be skill root** (`skills/omnifocus-manager/`) when running JXA scripts (legacy)
- **Skill-root-relative paths**: `loadLibrary('scripts/libraries/jxa/taskQuery.js')`
- **Commands use `${CLAUDE_PLUGIN_ROOT}`**: `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/`
- **No method destructuring**: `taskQuery.getInboxTasks(doc)`, never `const {getInboxTasks} = taskQuery`
- **Smoke test before version bump**: `bash scripts/test-queries.sh`
- **Always bump `.omnifocusjs` plugin version** on create/update — without it, OmniFocus won't recognize the plugin as an update

The `ofo` CLI sends stable JavaScript action scripts (in `scripts/omni-actions/`) to OmniFocus via `omnifocus://localhost/omnijs-run` URLs. Each script is approved once; variable data flows through the `&arg=` parameter. Results return via pasteboard (`Pasteboard.general.string` → `pbpaste`).

See `references/jxa_guide.md` for complete JXA reference and `loadLibrary` implementation.

---

## Reference Documentation

### Core Guides
- **[Official OmniFocus API](https://omni-automation.com/omnifocus/OF-API.html)** - Canonical API reference (verify here when unsure)
- **[API Reference](references/api_reference.md)** - Local quick lookup tables
- **[Omni Automation Guide](references/omni_automation_guide.md)** - Plugin development
- **[JXA Guide](references/jxa_guide.md)** - Command-line automation
- **[GTD Guide](references/gtd_guide.md)** - GTD-to-OmniFocus mapping

### Perspectives & Channels
- **[Perspective Creation](references/perspective_creation.md)** - Guided configuration (v4.2+)
- **[Perspective Templates](references/perspective_templates.md)** - 8 canonical GTD perspective JSON configs
- **[Channel Selection](references/channel_selection.md)** - Mac vs iOS routing, library composition, URL security
- **[URL Scheme Reference](references/omnifocus_url_scheme.md)** - Quick capture and linking

### Validation & Best Practices
- **[Code Generation Validation](references/code_generation_validation.md)** - TypeScript validation rules
- **[Automation Best Practices](references/automation_best_practices.md)** - Patterns and anti-patterns

### Technical References
- [omnifocus_api.md](references/omnifocus_api.md) - Full API specification
- [Omni Automation API Mapping](references/omni_automation_api_mapping.md) - JXA vs script URL API differences
- [Foundation Models Integration](references/foundation_models_integration.md) - Apple Intelligence (macOS 26+)
- [Example Plugin](references/example-plugin.ts) - Annotated TypeScript plugin template for new plugin development
- [Database Schema](references/database_schema.md), [Shared Classes](references/omni_automation_shared.md), [Insight Patterns](references/insight_patterns.md), [Workflows](references/workflows.md), [Troubleshooting](references/troubleshooting.md)

---

## Troubleshooting

See `references/troubleshooting.md` for permission issues, common errors, and debugging.

---

**Current version:** 9.3.0 — See README.md for version history.
