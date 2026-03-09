---
name: omnifocus-manager
description: |
  This skill should be used when working with OmniFocus data, running GTD diagnostics, configuring perspectives, or generating OmniFocus plugins. Triggers when user asks "show tasks", "overdue items", "check inbox", "stalled projects", "waiting for list", "someday maybe", "GTD health check", "create a plugin", "analyze OmniFocus", "AI Agent tasks", "publish plan to OmniFocus", "set up perspectives", "perspective inventory", "configure perspective", or "missing perspectives". Also triggers when the user pastes an `omnifocus://` URL — parse the entity type and ID from the URL, then use `/ofo:info <url>` to look it up directly. For pure GTD methodology coaching, use the gtd-coach skill instead.

  WORKFLOW: 1) CLASSIFY query vs plugin 2) SELECT format (solitary/solitary-fm/bundle/solitary-library) 3) COMPOSE from libraries 4) GENERATE via `node scripts/generate_plugin.js` - NEVER Write/Edit tools 5) VALIDATE via `bash scripts/validate-plugin.sh` 6) TEST in OmniFocus.
metadata:
  version: 6.6.1
  author: totally-tools
  license: MIT
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
- "show me", "what tasks", "analyze" → QUERY/EXECUTION (use manage_omnifocus.js, STOP)
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

### STEP 5: REPORT
```
✅ Plugin generated: <path>
✅ Validation: PASSED → Ready for installation
cp -r <path> ~/Library/Application\ Scripts/com.omnigroup.OmniFocus3/Plug-Ins/
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

### GTD-to-OmniFocus Quick Mapping

| GTD Concept | OmniFocus Implementation |
|-------------|--------------------------|
| Inbox | Inbox |
| Projects | Projects |
| Next Actions | Available tasks |
| Contexts | Tags |
| Waiting For | `@waiting` tag |
| Someday/Maybe | On Hold status |
| Weekly Review | Review perspective |

For detailed mapping, see `references/gtd_guide.md`.
For channel selection (Mac vs iOS routing), see `references/channel_selection.md`.

---

## Quick Decision Tree

### 0. ofo CLI (Preferred for Core CRUD)

The `ofo` CLI executes Omni Automation scripts directly inside OmniFocus via script URLs. It avoids JXA permission issues and provides clean ergonomics. **Use ofo for all task CRUD and queries when possible.**

```bash
scripts/ofo info <id-or-omnifocus-url>       # Task/project details
scripts/ofo complete <id-or-omnifocus-url>   # Mark task complete
scripts/ofo create --name "Task" --project "Work" --due 2026-12-31
scripts/ofo update <id> --name "New name" --flagged
scripts/ofo search "meeting"                 # Search by name/note
scripts/ofo list inbox                       # List inbox tasks
scripts/ofo list today                       # Flagged + due today
scripts/ofo list overdue                     # Past due date
scripts/ofo list flagged                     # All flagged active tasks
```

**Prerequisites:** OmniFocus running + external scripts enabled. Run `scripts/ofo setup` once to approve all action scripts.

### 1. Query OmniFocus Data (JXA — for advanced queries not covered by ofo)

**GTD diagnostics:**
```bash
osascript -l JavaScript scripts/gtd-queries.js --action system-health
osascript -l JavaScript scripts/gtd-queries.js --action stalled-projects
osascript -l JavaScript scripts/gtd-queries.js --action waiting-for
osascript -l JavaScript scripts/gtd-queries.js --action someday-maybe
osascript -l JavaScript scripts/gtd-queries.js --action recently-completed --days 7
osascript -l JavaScript scripts/gtd-queries.js --action neglected-projects --threshold 30
osascript -l JavaScript scripts/gtd-queries.js --action folder-structure
```

**Task queries (legacy — prefer ofo CLI above):**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js today
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
osascript -l JavaScript scripts/manage_omnifocus.js search --query "meeting"
```

**Create/modify tasks (legacy — prefer ofo CLI above):**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create --name "Task" --project "Work" --due "2025-12-31"
osascript -l JavaScript scripts/manage_omnifocus.js create --parent-id lz6kHB1apf5 --name "Subtask" --estimate 10m --tags Routine
```

**Project inspection & mutation:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js project-info --name "Project Name"
osascript -l JavaScript scripts/manage_omnifocus.js project-update --id <id> --review-interval 2weeks
osascript -l JavaScript scripts/manage_omnifocus.js batch-update --ids id1,id2,id3 --defer clear --due clear
```

**AI Agent project management:**
```bash
osascript -l JavaScript scripts/gtd-queries.js --action ai-agent-tasks
osascript -l JavaScript scripts/manage_omnifocus.js bulk-create --json-file /tmp/plan.json
osascript -l JavaScript scripts/gtd-queries.js --action repeating-tasks --days 90
osascript -l JavaScript scripts/gtd-queries.js --action analyze-projects --threshold 30
```

### 2. Manage Perspectives

```bash
osascript -l JavaScript scripts/gtd-queries.js --action perspective-inventory
osascript -l JavaScript scripts/perspective-config.js --action show --name "Next Actions"
osascript -l JavaScript scripts/perspective-config.js --action apply-template --name "Next Actions" --template next-actions
osascript -l JavaScript scripts/perspective-config.js --action apply --name "My View" --rules '[{"actionAvailability":"available"}]'
osascript -l JavaScript scripts/perspective-config.js --action list-templates
```

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

After installing Attache, you can remove: AITaskAnalyzer, CompletedTasksSummary, Overview, TodaysTasks.

See `references/foundation_models_integration.md` for Foundation Models API details.

---

## Script Conventions

- **Prefer ofo CLI** for task CRUD: `scripts/ofo <command>` (uses Omni Automation script URLs, no CWD dependency)
- **CWD must be skill root** (`skills/omnifocus-manager/`) when running JXA scripts (legacy)
- **Skill-root-relative paths**: `loadLibrary('scripts/libraries/jxa/taskQuery.js')`
- **Commands use `${CLAUDE_PLUGIN_ROOT}`**: `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/`
- **No method destructuring**: `taskQuery.getInboxTasks(doc)`, never `const {getInboxTasks} = taskQuery`
- **Smoke test before version bump**: `bash scripts/test-queries.sh`

The `ofo` CLI sends stable JavaScript action scripts (in `scripts/omni-actions/`) to OmniFocus via `omnifocus://localhost/omnijs-run` URLs. Each script is approved once; variable data flows through the `&arg=` parameter. Results return via pasteboard (`Pasteboard.general.string` → `pbpaste`).

See `references/jxa_guide.md` for complete JXA reference and `loadLibrary` implementation.

---

## Reference Documentation

### Core Guides
- **[API Reference](references/api_reference.md)** - Complete API with quick lookup tables
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
- [OmniFocus-API.md](references/OmniFocus-API.md) - Full API specification
- [Foundation Models Integration](references/foundation_models_integration.md) - Apple Foundation Models: availability check, Session API, Schema.fromJSON construction, async patterns (macOS 26+, Omni Automation only)
- [Database Schema](references/database_schema.md) - SQLite structure
- [Omni Automation Shared](references/omni_automation_shared.md) - Shared classes
- [Insight Patterns](references/insight_patterns.md) - Pattern detection
- [Workflows](references/workflows.md) - Automation patterns
- [Troubleshooting](references/troubleshooting.md) - Common issues

---

## Troubleshooting

**Permission Issues:**
- Automation: System Settings → Privacy & Security → Automation → Enable OmniFocus for Terminal
- Full Disk Access: Required for database queries only

**Common Errors:**
- "Not authorized" → Grant automation permission
- "Database not found" → Grant Full Disk Access
- "Multiple tasks found" → Use task ID instead of name
- `TypeError: undefined is not an object` → Library failed to load; check CWD is skill root

See `references/troubleshooting.md` for complete troubleshooting guide.

---

**Current version:** 6.6.1 — See IMPROVEMENT_PLAN.md for version history.
