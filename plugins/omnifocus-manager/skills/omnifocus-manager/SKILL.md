---
name: omnifocus-manager
description: |
  This skill should be used when working with OmniFocus data, running GTD diagnostics, or generating OmniFocus plugins. Triggers when user asks "show tasks", "overdue items", "check inbox", "stalled projects", "waiting for list", "someday maybe", "GTD health check", "create a plugin", "analyze OmniFocus", "AI Agent tasks", or "publish plan to OmniFocus". For pure GTD methodology coaching, use the gtd-coach skill instead.

  WORKFLOW: 1) CLASSIFY query vs plugin 2) SELECT format (solitary/solitary-fm/bundle/solitary-library) 3) COMPOSE from libraries 4) GENERATE via `node scripts/generate_plugin.js` - NEVER Write/Edit tools 5) VALIDATE via `bash scripts/validate-plugin.sh` 6) TEST in OmniFocus.
metadata:
  version: 6.0.0
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

## ⚡ CRITICAL: Plugin Generation Workflow (READ FIRST)

**If user requests "create plugin" or "make plugin", follow these EXACT steps:**

### STEP 1: CLASSIFY (No thinking required)
```
Keywords in request → Classification:
- "create plugin", "make plugin", "generate plugin" → PLUGIN GENERATION (continue to step 2)
- "show me", "what tasks", "analyze" → QUERY/EXECUTION (use manage_omnifocus.js, STOP)
```

### STEP 2: SELECT FORMAT (Choose one)
```
Plugin requirements → Format:
- Single action, no AI     → --format solitary
- Single action, with AI   → --format solitary-fm
- Multiple actions         → --format bundle --template <name>
- Library for reuse        → --format solitary-library
```

### STEP 3: INVOKE GENERATOR (MANDATORY - TypeScript validation automatic)
```bash
node scripts/generate_plugin.js --format <FORMAT> --name "<NAME>"
```

**🚫 RED FLAG:** If about to use Write or Edit tool for .js/.omnijs files → STOP, use generator instead

### STEP 4: VALIDATE (MANDATORY - Always run)
```bash
bash scripts/validate-plugin.sh <generated-plugin-path>
```

**Zero tolerance:** If validation fails, fix errors and re-validate before proceeding.

### STEP 5: REPORT SUCCESS
```
✅ Plugin generated: <path>
✅ TypeScript validation: PASSED
✅ Plugin validation: PASSED
✅ Ready for installation

Installation:
cp -r <path> ~/Library/Application\ Scripts/com.omnigroup.OmniFocus3/Plug-Ins/
```

---

**COMPLIANCE SELF-CHECK:**
- [ ] Used generate_plugin.js (NOT Write/Edit)
- [ ] TypeScript validation ran during generation
- [ ] Ran validate-plugin.sh after generation
- [ ] All validations passed
- [ ] Reported results to user

If you skipped ANY step above, you did it wrong. Go back and follow the workflow.

---

## Why TypeScript Validation is Mandatory

The generator (`scripts/generate_plugin.js`) automatically validates ALL generated code against:
- `typescript/omnifocus.d.ts` - Official OmniFocus API type definitions
- `typescript/omnifocus-extensions.d.ts` - Foundation Models API types

**This catches errors BEFORE they break in OmniFocus:**
- ❌ `FileSaver.show()` missing argument → ✅ `FileSaver.show(wrapper)`
- ❌ `task.name()` (method) → ✅ `task.name` (property)
- ❌ `new LanguageModel.Schema()` → ✅ `LanguageModel.Schema.fromJSON()`
- ❌ `Document.defaultDocument` (anti-pattern) → ✅ Use `flattenedTasks`

**Zero-tolerance policy:** Generator refuses to create plugins with TypeScript errors.

You don't need to understand TypeScript - the generator handles it automatically.

---

## What is OmniFocus?

**OmniFocus** is a task management application for macOS and iOS implementing the Getting Things Done (GTD) methodology. It helps capture, organize, and track tasks with projects, tags, perspectives, defer/due dates, and repeating tasks.

## What This Skill Does

This skill provides **execution-first architecture** for OmniFocus automation:

1. **Execute automation** - Run existing scripts and plugins
2. **Compose workflows** - Assemble patterns from modular libraries
3. **Understand GTD concepts** - Navigate OmniFocus and GTD methodology
4. **Analyze tasks with AI** - Use Apple Foundation Models for insights

**Execution priority:** 80% execute existing code, 15% compose from libraries, 5% generate new code.

---

## Four-Pillar Architecture

This skill covers three of four pillars. GTD coaching lives in a separate skill.

| Pillar | Capability | Owner |
|--------|-----------|-------|
| **1. Query** | JXA/Omni Automation live database queries | omnifocus-manager |
| **2. Perspectives** | Programmatic perspective creation | omnifocus-manager |
| **3. GTD Coaching** | Pure methodology coaching | **gtd-coach** skill |
| **4. Plugins + FM** | Plugin generation, Apple Intelligence | omnifocus-manager |

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

For detailed mapping and automation commands, see `references/gtd_guide.md`.

---

## Quick Decision Tree

**What do you want to do?**

### 1. Execute OmniFocus Operations

**GTD diagnostic queries (system health):**
```bash
osascript -l JavaScript scripts/gtd-queries.js --action inbox-count
osascript -l JavaScript scripts/gtd-queries.js --action stalled-projects
osascript -l JavaScript scripts/gtd-queries.js --action waiting-for
osascript -l JavaScript scripts/gtd-queries.js --action someday-maybe
osascript -l JavaScript scripts/gtd-queries.js --action neglected-projects --threshold 30
osascript -l JavaScript scripts/gtd-queries.js --action recently-completed --days 7
osascript -l JavaScript scripts/gtd-queries.js --action folder-structure
osascript -l JavaScript scripts/gtd-queries.js --action system-health
```

**Task queries (today/upcoming/flagged):**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js today
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
osascript -l JavaScript scripts/manage_omnifocus.js overdue
osascript -l JavaScript scripts/manage_omnifocus.js flagged
osascript -l JavaScript scripts/manage_omnifocus.js search --query "meeting"
```

**Create/modify tasks:**
```bash
# Quick capture (cross-platform)
open "omnifocus:///add?name=Task&autosave=true"

# Detailed creation (Mac only)
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Task" --project "Work" --due "2025-12-31"

# Add subtask to existing project or task by ID
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --parent-id lz6kHB1apf5 --name "Subtask" --estimate 10m --tags Routine
```

**Project inspection & mutation:**
```bash
# Get project details (subtasks, repeat rule, review interval)
osascript -l JavaScript scripts/manage_omnifocus.js project-info --name "Weekly Review"
osascript -l JavaScript scripts/manage_omnifocus.js project-info --id lz6kHB1apf5

# Update project properties
osascript -l JavaScript scripts/manage_omnifocus.js project-update --id lz6kHB1apf5 --review-interval 1month
osascript -l JavaScript scripts/manage_omnifocus.js project-update --id lz6kHB1apf5 --sequential
osascript -l JavaScript scripts/manage_omnifocus.js project-update --id lz6kHB1apf5 --note-remove-line "- Issue Status"

# Batch update (clear defer/due dates across multiple tasks)
osascript -l JavaScript scripts/manage_omnifocus.js batch-update --ids id1,id2,id3 --defer clear --due clear
```

**AI Agent project management:**
```bash
# Query all AI Agent-tagged projects with progress
osascript -l JavaScript scripts/gtd-queries.js --action ai-agent-tasks
osascript -l JavaScript scripts/gtd-queries.js --action ai-agent-tasks --child-tag "Claude Code"

# Bulk-create a project from JSON (used by /of:plan command)
osascript -l JavaScript scripts/manage_omnifocus.js bulk-create --json-file /tmp/plan.json
```

See `references/jxa_guide.md` for complete JXA reference.
See `references/omnifocus_url_scheme.md` for URL scheme.

### 2. Create or Modify Plugins

**→ See ⚡ CRITICAL workflow at top of this document**

Quick reference:
```bash
node scripts/generate_plugin.js --format <solitary|solitary-fm|bundle> --name "Plugin Name"
bash scripts/validate-plugin.sh <generated-plugin-path>
```

See `references/omni_automation_guide.md` for plugin development details.
See `references/code_generation_validation.md` for validation rules.

### 3. Automate via Scripts or URLs

**JXA (Mac command-line):** Use modular libraries from `scripts/libraries/jxa/`
See `references/jxa_guide.md` for complete reference.

**URL Scheme (cross-platform):** Perfect for embedding in notes.
See `references/omnifocus_url_scheme.md` for reference.

### 4. Understand GTD Methodology

For **pure GTD coaching** (principles, next action clarity, weekly review process, horizons of focus), use the **gtd-coach** skill.

For **GTD-to-OmniFocus mapping** (how GTD concepts map to OmniFocus features, automation commands), see `references/gtd_guide.md`.

### 5. Analyze Tasks for Insights

**AI-powered (OmniFocus 4.8+):**
Install `assets/AITaskAnalyzer.omnifocusjs` plugin.
Requires macOS 15.2+ with Apple Silicon.

See `references/foundation_models_integration.md` for details.

---

## Library Composition

**PHILOSOPHY:** Compose from libraries BEFORE generating new code.

### Available Libraries (`scripts/libraries/omni/`)

| Library | Functions |
|---------|-----------|
| `taskMetrics.js` | getTodayTasks, getOverdueTasks, getCompletedToday, getFlaggedTasks |
| `exportUtils.js` | toJSON, toCSV, toMarkdown, toHTML, toClipboard, toFile |
| `completedTasksFormatter.js` | formatAsMarkdown (with project grouping) |
| `patterns.js` | queryAndAnalyzeWithAI, queryAndExport, batchUpdate |
| `insightPatterns.js` | detectStalledProjects, detectWaitingForAging |
| `treeBuilder.js` | OmniFocus 4 tree API support (v4.1+) |

### Usage in Bundle Plugins

Declare in manifest.json:
```json
{
  "libraries": [
    { "identifier": "taskMetrics" },
    { "identifier": "exportUtils" }
  ]
}
```

Use in actions:
```javascript
const metrics = this.plugIn.library('taskMetrics');
const tasks = metrics.getTodayTasks();
```

See `scripts/libraries/README.md` for complete library documentation.

---

## Automation Approaches

| Approach | Platform | Use For |
|----------|----------|---------|
| **Omni Automation** | Mac + iOS | Reusable plugins, cross-platform |
| **JXA** | Mac only | Scripts, scheduled tasks, external automation |
| **URL Scheme** | Mac + iOS | Quick capture, embedding in notes |
| **Database** | Mac only | Complex SQL queries (last resort) |

See `references/omni_automation_guide.md` for Omni Automation.
See `references/jxa_guide.md` for JXA automation.
See `references/omnifocus_url_scheme.md` for URL scheme.

---

## Reference Documentation

### Core Guides
- **[API Reference](references/api_reference.md)** - Complete API with quick lookup tables
- **[Omni Automation Guide](references/omni_automation_guide.md)** - Plugin development
- **[JXA Guide](references/jxa_guide.md)** - Command-line automation
- **[GTD Guide](references/gtd_guide.md)** - GTD-to-OmniFocus mapping (see gtd-coach for methodology)

### Validation & Best Practices
- **[Code Generation Validation](references/code_generation_validation.md)** - Validation rules + TypeScript strategy
- **[Automation Best Practices](references/automation_best_practices.md)** - Patterns and anti-patterns

### Specialized Topics
- [Foundation Models Integration](references/foundation_models_integration.md) - Apple Intelligence
- [URL Scheme Reference](references/omnifocus_url_scheme.md) - Quick capture
- [Perspective Creation](references/perspective_creation.md) - Custom perspectives
- [Workflows](references/workflows.md) - Automation patterns
- [Troubleshooting](references/troubleshooting.md) - Common issues

### Technical References
- [OmniFocus-API.md](references/OmniFocus-API.md) - Full API specification
- [Database Schema](references/database_schema.md) - SQLite structure
- [Omni Automation Shared](references/omni_automation_shared.md) - Shared classes
- [Insight Patterns](references/insight_patterns.md) - Pattern detection

---

## Execution-First Philosophy

This skill prioritizes **executing existing code** over generating new code:

**Low-cost (80%):** Execute existing scripts, run installed plugins, use URL scheme
**Medium-cost (15%):** Compose from libraries, customize examples
**High-cost (5%):** Generate novel code (only when no pattern exists)

**Benefit:** Faster execution, lower token usage, tested code, consistent patterns.

---

## Common Use Cases

### "What should I work on today?"
```bash
osascript -l JavaScript scripts/manage_omnifocus.js today
```

### "Create a task"
```bash
open "omnifocus:///add?name=Task&autosave=true"
```

### "What's due this week?"
```bash
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
```

### "How's my GTD system?" / "Are my projects healthy?"
```bash
osascript -l JavaScript scripts/gtd-queries.js --action system-health
```

### "Show me a project's details / subtasks"
```bash
osascript -l JavaScript scripts/manage_omnifocus.js project-info --name "Project Name"
```

### "Change project review interval / ordering"
```bash
osascript -l JavaScript scripts/manage_omnifocus.js project-update --id <id> --review-interval 2weeks
```

### "Clear dates on multiple tasks at once"
```bash
osascript -l JavaScript scripts/manage_omnifocus.js batch-update --ids id1,id2,id3 --defer clear
```

### "Which projects are stalled?" / "No next actions?"
```bash
osascript -l JavaScript scripts/gtd-queries.js --action stalled-projects
```

### "What's in my Waiting For?" / "Aging waiting items?"
```bash
osascript -l JavaScript scripts/gtd-queries.js --action waiting-for
```

### "Show my someday/maybe list"
```bash
osascript -l JavaScript scripts/gtd-queries.js --action someday-maybe
```

### "Analyze my tasks for patterns"
Install `assets/AITaskAnalyzer.omnifocusjs` (OmniFocus 4.8+)

### "Create a plugin to show today's tasks"
```bash
node scripts/generate_plugin.js --format solitary --name "Todays Tasks"
```

---

## Script Conventions

Rules for creating and modifying JXA scripts in this skill:

- **CWD-relative `loadLibrary`**: All JXA scripts use `$.NSFileManager.defaultManager.currentDirectoryPath` to resolve library paths. CWD must be the skill root (`skills/omnifocus-manager/`) when any script runs. Shell callers are responsible for setting this.
- **Skill-root-relative paths**: Call `loadLibrary('scripts/libraries/jxa/taskQuery.js')` — path is relative to the skill root, not to the script file.
- **Shell wrappers cd to skill root**: Shell scripts that invoke JXA scripts `cd` to `skills/omnifocus-manager/` (the skill root), not into `scripts/`. Reference scripts as `scripts/gtd-queries.js`.
- **Commands use `${CLAUDE_PLUGIN_ROOT}`**: Command `.md` files reference scripts via `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/`.
- **No method destructuring**: Always call `taskQuery.getInboxTasks(doc)`, never `const {getInboxTasks} = taskQuery` — library methods use `this` internally.
- **Run smoke test before version bump**: `bash scripts/test-queries.sh` validates both entry-point scripts.

See `references/jxa_guide.md` § 7 for the canonical `loadLibrary` implementation to copy into new scripts.

---

## Troubleshooting

**Permission Issues:**
- Automation: System Settings → Privacy & Security → Automation → Enable OmniFocus for Terminal
- Full Disk Access: Required for database queries only

**Common Errors:**
- "Not authorized" → Grant automation permission
- "Database not found" → Grant Full Disk Access
- "Multiple tasks found" → Use task ID instead of name
- `TypeError: undefined is not an object (evaluating 'taskQuery.getXxx')` → Library failed to load; check that `loadLibrary` uses `$.getenv('_')` pattern (not CWD-based)

See `references/troubleshooting.md` for complete troubleshooting guide.

---

## Version Information

**Current version:** 5.5.0

**Recent changes:**
- v5.3.0: Add project-info, project-update, batch-update commands; create --parent-id (#68)
- v5.2.0: Unify manage_omnifocus.js with JXA library; delete omnifocus.js; single source of truth
- v5.1.0: Add gtd-queries.js with 8 GTD diagnostic actions; 7 new taskQuery project-level functions
- v5.0.0: Split GTD coaching into gtd-coach skill, four-pillar architecture (#63)
- v4.5.0: AITaskAnalyzer v3.4.0: dailyReview + weeklyReview actions (#62)
- v4.4.0: Deterministic plugin generation workflow, Agent Skill compliance
- v4.1.0: OmniFocus 4 tree API support, treeBuilder library
- v4.0.0: TypeScript-based plugin generation with LSP validation

---

## External Resources

- **Omni Automation:** [omni-automation.com/omnifocus](https://omni-automation.com/omnifocus/)
- **OmniFocus URL Schemes:** [support.omnigroup.com/omnifocus-url-schemes](https://support.omnigroup.com/omnifocus-url-schemes/)
- **GTD Methodology:** [gettingthingsdone.com](https://gettingthingsdone.com)
