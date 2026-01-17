---
name: omnifocus-manager
description: |
  Query and manage OmniFocus tasks through database queries and JavaScript for Automation (JXA).

  WORKFLOW: 1) CLASSIFY query vs plugin 2) SELECT format (solitary/solitary-fm/bundle/solitary-library) 3) COMPOSE from libraries (taskMetrics, exportUtils, patterns) 4) GENERATE via `node scripts/generate_plugin.js` - NEVER Write/Edit tools 5) CUSTOMIZE action files 6) TEST in OmniFocus. TypeScript generator validates during generation. Manual creation creates broken plugins.

  This skill should be used when working with OmniFocus data, creating or modifying tasks, analyzing task lists, searching for tasks, or automating OmniFocus workflows. Triggers when user mentions OmniFocus, tasks, projects, GTD workflows, or asks to create, update, search, or analyze their task data.
metadata:
  version: 4.2.0
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

## MANDATORY PLUGIN GENERATION WORKFLOW

When user requests plugin creation, follow these steps:

### WORKFLOW (DO NOT SKIP):

**1. CLASSIFY REQUEST**
- Keywords: "create a plugin", "make a plugin" → Plugin Creation
- Keywords: "show me", "what are", "analyze" → Execute JXA script, STOP

**2. SELECT FORMAT**
- ONE action, no AI → `--format solitary`
- ONE action, with AI → `--format solitary-fm`
- MULTIPLE actions → `--format bundle --template query-simple`
- LIBRARY code → `--format solitary-library`

**3. CHECK LIBRARIES** (`scripts/libraries/omni/`)
- `taskMetrics.js` - getTodayTasks, getOverdueTasks, getCompletedToday
- `exportUtils.js` - toJSON, toCSV, toMarkdown, toHTML
- `patterns.js` - queryAndAnalyzeWithAI, queryAndExport

**4. INVOKE GENERATOR**
```bash
node scripts/generate_plugin.js --format solitary --name "My Plugin"
```
- **ALWAYS** use the generator - **NEVER** use Write/Edit tools for plugins
- Generator validates automatically via TypeScript Compiler API

**5. CUSTOMIZE (if needed)**
- Edit action logic to add library calls
- Test in Automation Console (`Cmd+Opt+Shift+C`) first

**6. TEST IN OMNIFOCUS**
```bash
cp -r *.omnifocusjs ~/Library/Application\ Scripts/com.omnigroup.OmniFocus3/Plug-Ins/
```

### WHY MANDATORY:

| TypeScript Generator | Manual Creation |
|---------------------|-----------------|
| Validates during generation | No validation |
| Type-checks against omnifocus.d.ts | Broken code |
| Zero-tolerance (refuses on errors) | Runtime failures |
| Creates working plugins | Missing dependencies |

---

## Quick Decision Tree

**What do you want to do?**

### 1. Execute OmniFocus Operations

**Query tasks (read data):**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js today
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
osascript -l JavaScript scripts/manage_omnifocus.js search --query "meeting"
```

**Create/modify tasks:**
```bash
# Quick capture (cross-platform)
open "omnifocus:///add?name=Task&autosave=true"

# Detailed creation (Mac only)
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Task" --project "Work" --due "2025-12-31"
```

See `references/jxa_guide.md` for complete JXA reference.
See `references/omnifocus_url_scheme.md` for URL scheme.

### 2. Create or Modify Plugins

**Generate plugin (recommended):**
```bash
node scripts/generate_plugin.js --format solitary --name "My Plugin"
node scripts/generate_plugin.js --format solitary-fm --name "AI Analyzer"
node scripts/generate_plugin.js --format bundle --template query-simple --name "Task Tools"
```

See `references/omni_automation_guide.md` for plugin development.
See `references/code_generation_validation.md` for validation rules.

**TypeScript Development:** The `typescript/` directory contains:
- `omnifocus.d.ts` - Official OmniFocus API type definitions
- `omnifocus-extensions.d.ts` - LanguageModel API for Apple Intelligence

### 3. Automate via Scripts or URLs

**JXA (Mac command-line):** Use modular libraries from `scripts/libraries/jxa/`
See `references/jxa_guide.md` for complete reference.

**URL Scheme (cross-platform):** Perfect for embedding in notes.
See `references/omnifocus_url_scheme.md` for reference.

### 4. Understand OmniFocus and GTD

See `references/gtd_guide.md` for complete GTD methodology including:
- GTD principles and implementation
- OmniFocus perspectives
- Common pitfalls

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
- **[GTD Guide](references/gtd_guide.md)** - GTD methodology

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

### "Analyze my tasks for patterns"
Install `assets/AITaskAnalyzer.omnifocusjs` (OmniFocus 4.8+)

### "Create a plugin to show today's tasks"
```bash
node scripts/generate_plugin.js --format solitary --name "Todays Tasks"
```

---

## Troubleshooting

**Permission Issues:**
- Automation: System Settings → Privacy & Security → Automation → Enable OmniFocus for Terminal
- Full Disk Access: Required for database queries only

**Common Errors:**
- "Not authorized" → Grant automation permission
- "Database not found" → Grant Full Disk Access
- "Multiple tasks found" → Use task ID instead of name

See `references/troubleshooting.md` for complete troubleshooting guide.

---

## Version Information

**Current version:** 4.2.0

**Recent changes:**
- v4.2.0: Consolidated references, integrated TypeScript validation strategy
- v4.1.0: OmniFocus 4 tree API support, treeBuilder library
- v4.0.0: TypeScript-based plugin generation with LSP validation

---

## External Resources

- **Omni Automation:** [omni-automation.com/omnifocus](https://omni-automation.com/omnifocus/)
- **OmniFocus URL Schemes:** [support.omnigroup.com/omnifocus-url-schemes](https://support.omnigroup.com/omnifocus-url-schemes/)
- **GTD Methodology:** [gettingthingsdone.com](https://gettingthingsdone.com)
