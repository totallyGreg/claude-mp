---
name: omnifocus-manager
description: |
  Query and manage OmniFocus tasks through database queries and JavaScript for Automation (JXA).

  WORKFLOW: 1) CLASSIFY query vs plugin 2) SELECT format (solitary/solitary-fm/bundle/solitary-library) 3) COMPOSE from libraries (taskMetrics, exportUtils, patterns) 4) GENERATE via `node scripts/generate_plugin.js` - NEVER Write/Edit tools 5) CUSTOMIZE action files 6) TEST in OmniFocus. TypeScript generator validates during generation. Manual creation creates broken plugins.

  This skill should be used when working with OmniFocus data, creating or modifying tasks, analyzing task lists, searching for tasks, or automating OmniFocus workflows. Triggers when user mentions OmniFocus, tasks, projects, GTD workflows, or asks to create, update, search, or analyze their task data.
metadata:
  version: 4.1.0
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

**OmniFocus** is a task management application for macOS and iOS that implements the Getting Things Done (GTD) methodology. It helps you capture, organize, and track tasks, projects, and goals with features like projects, tags, perspectives, defer/due dates, and repeating tasks.

When you strip down OmniFocus to its essence, you’ll find a few simple concepts:

- That big projects can be broken down into smaller tasks to make them easier to tackle.
- That those tasks can be categorized to help you tackle them more efficiently.
- That our computing devices can take some of the load off our overwhelmed minds by tracking when tasks will become available and when they’re due.
- And that this sort of trusted system works best when it can quickly and easily capture whatever is on your mind, while also giving you tools to review your system to regain control and focus.

## What This Skill Does

This skill provides **execution-first architecture** for OmniFocus automation with four equal capabilities:

1. **Execute automation** - Run existing scripts and plugins to query/modify tasks
2. **Compose workflows** - Assemble patterns from modular libraries
3. **Understand GTD concepts** - Navigate OmniFocus and Getting Things Done methodology
4. **Analyze tasks with AI** - Use Apple Foundation Models for intelligent insights

**Execution priority:** 80% execute existing code, 15% compose from libraries, 5% generate new code.

**Key principle:** Use modular libraries and existing scripts instead of generating from scratch.

---

## ⚠️ MANDATORY PLUGIN GENERATION WORKFLOW

When user requests plugin creation, follow these steps:

### WORKFLOW (DO NOT SKIP):

**1. CLASSIFY REQUEST**
→ Use REQUEST CLASSIFICATION section
→ Confirm: ONE-TIME query OR REUSABLE plugin?
→ If ONE-TIME, execute script and STOP

**2. SELECT FORMAT**
→ Use PLUGIN FORMAT SELECTION decision tree
→ Determine: solitary / solitary-fm / bundle / solitary-library
→ If bundle, select template: query-simple or stats-overview

**3. CHECK LIBRARIES**
→ Use LIBRARY COMPOSITION PRIORITY
→ Identify existing libraries covering requirements
→ List libraries to declare in manifest.json (bundle only)

**4. INVOKE GENERATOR**
→ **ALWAYS** use: `node scripts/generate_plugin.js`
→ **NEVER** use Write/Edit tools to create .omnijs or .omnifocusjs files
→ Pass correct parameters: --format, --name, (--template if bundle)
→ Generator validates automatically - no separate validation needed

**5. CUSTOMIZE (if needed)**
→ Read generated plugin code
→ Edit action logic to add library calls from Step 3
→ **If creating new libraries**: Test in Automation Console first
→ **Keep bundle clean**: No .eslintrc, validation scripts, or test files

**6. TEST IN OMNIFOCUS**
→ Install: `cp -r *.omnifocusjs ~/Library/Application Scripts/com.omnigroup.OmniFocus3/Plug-Ins/`
→ Restart OmniFocus
→ Test in Automation Console (`⌘⌥⇧C`) before full install
→ Verify plugin appears in Automation menu and works correctly

### WHY MANDATORY:

✅ **TypeScript generator:**

- Validates code during generation (TypeScript Compiler API)
- Type-checks against omnifocus.d.ts
- Zero-tolerance (refuses to generate if errors exist)
- Bundles libraries correctly (manifest.json + Resources/)
- Creates working plugins on first try

❌ **Manual creation fails:**

- No validation → broken code
- Library bundling errors → missing dependencies
- Example: Manual plugins fail to install

### ⛔ NEVER:

- ❌ Create manifest.json with Write tool
- ❌ Create action.js files with Write tool
- ❌ Skip TypeScript validation

### ✅ ALWAYS:

- ✅ Use `node scripts/generate_plugin.js`
- ✅ Let generator create all files
- ✅ Test in OmniFocus before claiming success

---

## 🧪 VALIDATION & QUALITY ASSURANCE

### After Skill Modifications

**Quick validation (structure only):**

```bash
python3 /Users/gregwilliams/Documents/Projects/claude-mp/skills/skillsmith/scripts/evaluate_skill.py \
  /Users/gregwilliams/Documents/Projects/claude-mp/skills/omnifocus-manager --quick
```

**Checks:** SKILL.md frontmatter, required fields, spec compliance

**When to run:** After any SKILL.md changes

### Plugin Validation

**All validation happens in the generator:**

- TypeScript generator (`scripts/generate_plugin.ts`) validates during generation
- Uses TypeScript Compiler API for syntax and type checking
- Checks against `omnifocus.d.ts` and `omnifocus-extensions.d.ts`
- Refuses to generate if any errors exist (zero-tolerance)
- No separate validation tools needed

**When creating complex plugins with custom libraries:**

⚠️ **If you need to manually create library files:**

1. **DON'T**: Create separate validation scripts or test files
2. **DO**: Test in OmniFocus Automation Console (`⌘⌥⇧C`)
3. **DO**: Add validation checks to the generator if insufficient
4. **DO**: Keep plugin bundles clean (no .eslintrc, test scripts, etc.)

**Plugin bundle should only contain:**

- `manifest.json` (generated)
- `Resources/` directory with `.js` action files
- `README.md` (user documentation)
- `INSTALL.md` (installation instructions - optional)
- `TROUBLESHOOTING.md` (troubleshooting guide - optional)

**Success criteria:**

- ✅ Generator reports "TypeScript validation passed"
- ✅ Plugin installs without errors
- ✅ Appears in OmniFocus Automation menu
- ✅ Executes without runtime errors

---

## Quick Decision Tree

**START HERE: What do you want to do?**

## 🚦 REQUEST CLASSIFICATION: Query vs Plugin Creation

Determine user intent BEFORE taking action:

**ONE-TIME Query** (Execute existing script):

- Keywords: "show me", "what are", "analyze", "find", "list", "tell me"
- Examples: "Show me today's tasks" → Execute JXA script
- Action: Use `osascript -l JavaScript scripts/manage_omnifocus.js`

**REUSABLE Plugin** (Generate plugin):

- Keywords: "create a plugin", "make a plugin", "automate", "create an action"
- Examples: "Create a plugin to show today's tasks" → Generate plugin
- Action: Use `node scripts/generate_plugin.js`

**Decision Rule:**

```
IF request contains ["create a plugin", "make a plugin", "automate", "build automation"]
THEN → Plugin Creation Workflow
ELSE → Query Execution Workflow
```

**If ambiguous, ask user:**
"Do you want me to:
A) Show you this data now (one-time query), or
B) Create a reusable plugin for future use?"

---

## 🔀 PLUGIN FORMAT SELECTION

**Q1: How many actions?**

- ONE action, no AI → `--format solitary`
- ONE action, with AI → `--format solitary-fm`
- MULTIPLE actions → `--format bundle --template query-simple`
- LIBRARY code (no UI) → `--format solitary-library`

**Format Quick Reference:**
| Format | Use When | Command |
|--------|----------|---------|
| solitary | Single action, no AI | `node scripts/generate_plugin.js --format solitary --name "Name"` |
| solitary-fm | Single action with Apple Intelligence | `node scripts/generate_plugin.js --format solitary-fm --name "Name"` |
| bundle | Multiple actions or localization | `node scripts/generate_plugin.js --format bundle --template query-simple --name "Name"` |
| solitary-library | Reusable library code | `node scripts/generate_plugin.js --format solitary-library --name "Name"` |

**Examples:**

- "Plugin to show flagged tasks" → solitary (1 action, no AI)
- "AI task analyzer" → solitary-fm (1 action, needs AI)
- "Plugin with copy and save actions" → bundle (2 actions)

---

### 1. Execute OmniFocus Operations

**Query tasks (read data):**

```bash
# Use existing JXA script
osascript -l JavaScript scripts/manage_omnifocus.js today
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
osascript -l JavaScript scripts/manage_omnifocus.js search --query "meeting"
```

→ **See:** [JXA API Guide](references/jxa_api_guide.md#cli-command-reference)

**Create/modify tasks (write data):**

```bash
# Quick capture (cross-platform)
open "omnifocus:///add?name=Task&autosave=true"

# Detailed creation (Mac only)
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Task" --project "Work" --due "2025-12-31"
```

→ **See:** [URL Scheme Guide](references/omnifocus_url_scheme.md) or [JXA API Guide](references/jxa_api_guide.md#task-management-commands)

**Run existing plugins:**

- Install `assets/TodaysTasks.omnifocusjs` - Today's task viewer
- Install `assets/AITaskAnalyzer.omnifocusjs` - AI-powered analysis

→ **See:** [Plugin Installation Guide](references/plugin_installation.md)

### 2. Create or Modify Plugins

> ⚠️ **CRITICAL: Plugin Code Generation with TypeScript**
>
> **The skill now uses TypeScript-based plugin generation with LSP validation:**
>
> 1. TypeScript generator validates code DURING generation (not after)
> 2. Type definitions catch API errors before file creation
> 3. Generated plugins include type annotations for better documentation
>
> **Before generating plugins:**
>
> 1. Read `references/code_generation_validation.md` - Validation guidelines
> 2. Verify APIs in `references/api_quick_reference.md` - Prevent hallucinated APIs
> 3. Use TypeScript generator - Automatic validation included
>
> **TypeScript Development Environment:** `typescript/` directory contains:
>
> - `omnifocus.d.ts` - Official OmniFocus API type definitions (1,698 lines)
> - `omnifocus-extensions.d.ts` - LanguageModel API for Apple Intelligence
> - `tsconfig.json` - TypeScript configuration
> - `README.md` - Setup guide for LSP development

**New to plugins? Start here:**
→ **[Plugin Quickstart](references/quickstarts/plugin_quickstart.md)** - 5-minute tutorial

**Quick Plugin Generation with TypeScript (Recommended - <1 minute):**

```bash
# Generate plugin from TypeScript template
node scripts/generate_plugin.js --format solitary --name "My Plugin"
node scripts/generate_plugin.js --format solitary-fm --name "AI Analyzer"
node scripts/generate_plugin.js --format solitary-library --name "My Utils"

# Available formats:
# - solitary: Single-file action plugin (.omnijs)
# - solitary-fm: Action with Foundation Models/Apple Intelligence
# - solitary-library: Single-file library plugin
# - bundle: Bundle plugin with localization (requires --template)
```

**Benefits:**

- ✅ TypeScript LSP validation during generation
- ✅ Type-safe API usage (catches errors before file creation)
- ✅ Type annotations in generated code (inline documentation)
- ✅ Correct API patterns (validated against .d.ts files)
- ✅ <1 minute generation time

→ **See:** Run `node scripts/generate_plugin.js --help` for all options
→ **TypeScript Guide:** `typescript/README.md` for manual development with LSP

**Create from template manually:**

1. Reference `assets/OFBundlePlugInTemplate.omnifocusjs` - official Omni Group template
2. Or copy from `assets/plugin-templates/` - validated examples
3. Modify manifest.json and action scripts
4. Load libraries via `this.plugIn.library("libraryName")`

→ **See:** [Plugin Development Guide](references/plugin_development_guide.md)
→ **Templates:** [plugin-templates](assets/plugin-templates/) - Validated examples

**Modify existing plugin:**

1. Right-click `.omnifocusjs` → Show Package Contents
2. Edit `manifest.json` or `Resources/*.js` files
3. Restart OmniFocus to reload

→ **See:** [Plugin Development Guide](references/plugin_development_guide.md#modifying-plugins)

**Plugin Code Generation with TypeScript (RECOMMENDED WORKFLOW):**

⚠️ **IMPORTANT:** The TypeScript generator validates code automatically during generation.

**TypeScript Generator Workflow (AUTOMATED):**

**Step 1: Generate Plugin**

```bash
node scripts/generate_plugin.js --format solitary --name "My Plugin"
```

**What happens automatically:**

1. ✅ Loads TypeScript template with type annotations
2. ✅ Substitutes variables (name, identifier, etc.)
3. ✅ Validates syntax against TypeScript Compiler API
4. ✅ Checks code against omnifocus.d.ts and omnifocus-extensions.d.ts
5. ✅ Refuses to generate if validation fails (zero-tolerance)
6. ✅ Auto-renames .ts → .omnijs for deployment

**Step 2: Install and Test**

```bash
# Generated plugin is ready for installation
cp assets/MyPlugin.omnijs ~/Library/Application\ Scripts/com.omnigroup.OmniFocus3/Plug-Ins/
```

**Optional: Manual TypeScript Development with LSP**

For manual plugin development with full LSP support (autocomplete, type-checking):

**Step 1: Set Up TypeScript Environment**

1. Read `typescript/README.md` for setup instructions
2. Install TypeScript Language Server (if not already installed):
   ```bash
   sudo npm install -g typescript typescript-language-server
   ```

**Step 2: Develop with TypeScript**

1. Create `.ts` file in `typescript/` directory
2. Use LSP for autocomplete and type-checking while coding
3. TypeScript validates against `omnifocus.d.ts` and `omnifocus-extensions.d.ts`

**Step 3: Deploy**

1. Rename `.ts` to `.omnijs` or `.omnifocusjs`
2. Install in OmniFocus Plug-Ins directory

**What TypeScript LSP catches during development:**

- ✅ Undefined APIs (hallucinated APIs like `Document.defaultDocument`, `Progress`)
- ✅ Type mismatches (passing function when Version expected)
- ✅ Incorrect constructor arguments
- ✅ Property/method confusion (calling property as method)
- ✅ Syntax errors (`.bind(this)` on arrow functions)
- ✅ Semantic errors

**Legacy Validation (Manual Code Only):**

If generating code manually without TypeScript generator:

```bash
# ESLint validation (catches undefined globals, syntax errors)
eslint_d assets/YourPlugin.omnifocusjs/Resources/*.js
```

**Complete documentation:**

- TypeScript guide: `typescript/README.md`
- Validation rules: `references/code_generation_validation.md`
- Plugin patterns: `references/plugin_development_guide.md`
- API reference: `references/OmniFocus-API.md`, `references/api_quick_reference.md`

### 3. Automate via Scripts or URLs

**New to JXA? Start here:**
→ **[JXA Quickstart](references/quickstarts/jxa_quickstart.md)** - 5-minute tutorial

**Command-line automation (Mac only):**

- Use modular libraries from `scripts/libraries/jxa/`
- See examples in `assets/examples/jxa-scripts/`

→ **See:** [JXA API Guide](references/jxa_api_guide.md)

**Cross-platform quick capture:**

- Use URL scheme for task creation
- Perfect for embedding in notes (Obsidian, etc.)

→ **See:** [URL Scheme Guide](references/omnifocus_url_scheme.md)

**Automation workflows:**
→ **See:** [Workflows Guide](references/workflows.md)

### 4. Understand OmniFocus and GTD

**New to GTD? Start here:**
→ **[GTD Overview](references/gtd_overview.md)** - Navigation hub for all GTD resources

**Quick reference:**

- [GTD Context](references/gtd_context.md) - Brief principles overview
- [GTD Methodology](references/gtd_methodology.md) - Complete implementation guide
- [Workflows](references/workflows.md) - Practical automation patterns

**Learn OmniFocus concepts:**

- Projects vs Tasks vs Tags
- Perspectives and views
- Defer/due dates
- Sequential vs parallel projects

→ **See:** [GTD Overview](references/gtd_overview.md)

### 5. Analyze Tasks for Insights

**AI-powered analysis (OmniFocus 4.8+):**

- Install `assets/AITaskAnalyzer.omnifocusjs` plugin
- Requires macOS 15.2+ / iOS 18.2+ with Apple Silicon

→ **See:** [Foundation Models Integration](references/foundation_models_integration.md)

**Pattern detection (works on all versions):**

```bash
# Detect stalled projects, over-committed, etc.
python3 scripts/analyze_insights.py
```

→ **See:** [Insight Patterns Guide](references/insight_patterns.md)

---

## 🧩 LIBRARY COMPOSITION PRIORITY

**PHILOSOPHY:** Compose from libraries BEFORE generating new code

### Available Libraries (`scripts/libraries/omni/`):

- `taskMetrics.js` - getTodayTasks, getOverdueTasks, getCompletedToday, getFlaggedTasks
- `exportUtils.js` - toJSON, toCSV, toMarkdown, toHTML, toClipboard, toFile
- `completedTasksFormatter.js` - formatAsMarkdown (with project grouping)
- `patterns.js` - queryAndAnalyzeWithAI, queryAndExport, batchUpdate
- `insightPatterns.js` - detectStalledProjects, detectWaitingForAging

### Workflow:

1. **Check libraries** - Does functionality already exist?
2. **Declare in manifest** - Add to "libraries" array (bundle plugins only)
3. **Use in actions** - Call via `this.plugIn.library("libName")`

**Example:** "Create plugin to show completed tasks"

- ✅ Use: `taskMetrics.getCompletedToday()` + `completedTasksFormatter.formatAsMarkdown()`
- ❌ Don't: Generate new completion-checking code from scratch

**For bundle plugins**, declare in manifest.json:

```json
{
  "libraries": [
    { "identifier": "taskMetrics" },
    { "identifier": "completedTasksFormatter" },
    { "identifier": "exportUtils" }
  ]
}
```

---

## Modular Library System

**Instead of generating code from scratch, use the modular library system:**

**Location:** `scripts/libraries/`

**Available libraries:**

**JXA Libraries** (Mac command-line):

- `taskQuery.js` - Query operations (today, overdue, flagged, search)
- `taskMutation.js` - Create, update, complete, delete tasks
- `dateUtils.js` - Date parsing and formatting
- `argParser.js` - Command-line argument parsing

**Omni Libraries** (Mac + iOS plugins):

- `taskMetrics.js` - Task data collection (PlugIn.Library)
- `treeBuilder.js` - ⭐ **NEW v4.1** - OmniFocus 4 tree API support (PlugIn.Library)
  - Database tree building with metrics/health integration
  - Export to Markdown/JSON/OPML formats for outliner apps
  - Window tree manipulation (reveal/select/expand/collapse nodes)
  - Graceful degradation for OmniFocus 3 (exports work, window ops require OF4)
  - **See:** TreeExplorer.omnifocusjs plugin for usage examples
- `exportUtils.js` - Export to JSON/CSV/Markdown/HTML (PlugIn.Library)
- `insightPatterns.js` - Pattern detection (PlugIn.Library)
- `templateEngine.js` - Template-based task creation (PlugIn.Library)
- `patterns.js` - ⭐ MCP-ready composable patterns with Foundation Models (PlugIn.Library)

**Shared Libraries** (Cross-platform):

- `urlBuilder.js` - URL scheme helper

**See complete documentation:** [Libraries README](scripts/libraries/README.md)

### Usage Patterns

**Pattern 1: Standalone (load and call):**

```javascript
const taskQuery = loadLibrary('scripts/libraries/jxa/taskQuery.js')
const tasks = taskQuery.getTodayTasks(doc)
```

**Pattern 2: JXA Scripts (compose workflow):**

```javascript
#!/usr/bin/osascript -l JavaScript
const taskQuery = loadLibrary('scripts/libraries/jxa/taskQuery.js')
const tasks = taskQuery.getTodayTasks(app.defaultDocument)
// ... use tasks
```

**Pattern 3: OmniFocus Plugins (PlugIn.Library):**

```javascript
// In manifest.json: "libraries": ["taskMetrics"]
const metrics = this.plugIn.library('taskMetrics')
const tasks = metrics.getTodayTasks()
```

**See examples:** `assets/examples/` directory

---

## Examples and Templates

**All examples are in:** `assets/examples/`

**Standalone** - Minimal library usage:

- `query-today.js` - Load taskQuery, get today's tasks
- `create-task.js` - Load taskMutation, create task
- `build-url.js` - Load urlBuilder, generate URL

**JXA Scripts** - Complete workflows:

- `check-today.js` - Daily task report with priorities
- `bulk-create.js` - Create multiple tasks from templates
- `weekly-review.js` - Complete GTD weekly review
- `generate-report.js` - Export tasks to various formats

**Plugins** - Reusable OmniFocus actions:

- `SimpleQuery.omnifocusjs` - Query using taskMetrics library
- `BulkOperations.omnifocusjs` - Batch operations using patterns library
- `URLGenerator.omnifocusjs` - URL generation using urlBuilder library

**See:** [Examples README](assets/examples/README.md)

---

## Automation Approaches

### 1. Omni Automation (Recommended for Plugins)

**Platform:** Mac + iOS + iPadOS
**Environment:** Runs within OmniFocus
**Permissions:** None required
**Use for:** Reusable plugins, cross-platform automation

**Features:**

- Cross-platform (Mac + iOS)
- PlugIn.Library pattern for modular code
- Direct property access: `task.name` (not `task.name()`)
- UI components (Alert, Form, FileSaver)
- Apple Foundation Models integration (OmniFocus 4.8+)

**Get started:** [Plugin Quickstart](references/quickstarts/plugin_quickstart.md)

**Complete guide:** [Plugin Development Guide](references/plugin_development_guide.md)

### 2. JXA (JavaScript for Automation)

**Platform:** Mac only
**Environment:** Command line
**Permissions:** Automation permission required
**Use for:** Scripts, scheduled tasks, external automation

**Features:**

- Full AppleScript API access
- Method call syntax: `task.name()` (not `task.name`)
- Modular libraries (taskQuery, taskMutation, dateUtils)
- Integration with shell scripts, cron, Alfred, etc.

**Get started:** [JXA Quickstart](references/quickstarts/jxa_quickstart.md)

**Complete guide:** [JXA API Guide](references/jxa_api_guide.md)

### 3. URL Scheme

**Platform:** Mac + iOS + iPadOS
**Environment:** System-wide URLs
**Permissions:** None required
**Use for:** Quick capture, embedding in notes, shortcuts

**Features:**

- Fastest task creation
- Perfect for embedding in Markdown notes
- Bulk import via TaskPaper format
- Open perspectives (inbox, flagged, forecast, custom)
- x-callback-url support

**Complete guide:** [URL Scheme Reference](references/omnifocus_url_scheme.md)

### 4. Database Queries (Last Resort)

**Platform:** Mac only
**Environment:** Python scripts
**Permissions:** Full Disk Access required
**Use for:** Complex SQL queries when JXA insufficient

**Note:** Use JXA when possible. Database is read-only.

---

## Reference Documentation

### Quickstart Guides (5 minutes)

- **[Plugin Quickstart](references/quickstarts/plugin_quickstart.md)** - Your first plugin in 5 minutes
- **[JXA Quickstart](references/quickstarts/jxa_quickstart.md)** - JXA automation in 5 minutes

### Comprehensive Guides

**Plugin Development:**

- **[Plugin Development Guide](references/plugin_development_guide.md)** - Complete plugin creation guide
- [Plugin Installation](references/plugin_installation.md) - Installing and using plugins

**Automation:**

- **[JXA API Guide](references/jxa_api_guide.md)** - Complete JXA reference
- [Omni Automation Guide](references/omnifocus_automation.md) - Cross-platform automation
- [URL Scheme Reference](references/omnifocus_url_scheme.md) - Quick capture and embedding

**GTD Methodology:**

- **[GTD Overview](references/gtd_overview.md)** - Navigation hub for GTD resources
- [GTD Context](references/gtd_context.md) - Brief GTD principles
- [GTD Methodology](references/gtd_methodology.md) - Complete implementation guide
- [Workflows](references/workflows.md) - Practical automation patterns

**Advanced:**

- [Foundation Models Integration](references/foundation_models_integration.md) - AI-powered automation
- [Automation Best Practices](references/automation_best_practices.md) - Patterns and principles
- [Insight Patterns](references/insight_patterns.md) - Pattern detection catalog

### API References

- **[API Quick Reference](references/api_quick_reference.md)** - ⭐ Essential API patterns and anti-patterns
- [OmniFocus API](references/OmniFocus-API.md) - Complete API specification
- [Shared Classes](references/omni_automation_shared.md) - Alert, Form, FileSaver, etc.
- [Database Schema](references/database_schema.md) - SQLite structure
- [Perspective Creation](references/perspective_creation.md) - Custom perspectives

### Resources

- [Libraries README](scripts/libraries/README.md) - Modular library documentation
- [Examples README](assets/examples/README.md) - Working code examples
- [Assets README](assets/README.md) - Plugins and templates overview
- [Troubleshooting](references/troubleshooting.md) - Common issues and solutions

---

## Execution-First Philosophy

This skill prioritizes **executing existing code** over generating new code:

**Low-cost operations (80% of use cases):**

- Execute existing scripts: `osascript scripts/manage_omnifocus.js today`
- Run installed plugins: Click action in OmniFocus menu
- Use URL scheme: `open "omnifocus:///add?name=Task&autosave=true"`

**Medium-cost operations (15% of use cases):**

- Compose from libraries: Load taskQuery + taskMutation
- Customize examples: Copy from `assets/examples/` and modify
- Assemble patterns: Use patterns.js for complex workflows

**High-cost operations (5% of use cases):**

- Generate novel code: Only when no pattern exists
- Create new patterns: Offer to add to skill repertoire

**Benefit:** Faster execution, lower token usage, tested code, consistent patterns.

---

## Common Use Cases

### "What should I work on today?"

**Execute:**

```bash
osascript -l JavaScript scripts/manage_omnifocus.js today
```

Or install plugin: `assets/TodaysTasks.omnifocusjs`

### "Create a task"

**Quick (URL):**

```bash
open "omnifocus:///add?name=Task&autosave=true"
```

**Detailed (JXA):**

```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Task" --project "Work" --due "2025-12-31"
```

### "What's due this week?"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
```

### "Analyze my tasks for patterns"

**AI-powered (OmniFocus 4.8+):**
Install and run `assets/AITaskAnalyzer.omnifocusjs`

**Pattern detection (all versions):**

```bash
python3 scripts/analyze_insights.py
```

### "Create a weekly review plugin"

**Compose from example:**

1. Copy `assets/examples/plugins/SimpleQuery.omnifocusjs`
2. Modify for weekly review workflow
3. Use libraries: taskMetrics, exportUtils, insightPatterns

---

## Troubleshooting

### Permission Issues

**Automation Permission (JXA):**

- System Settings → Privacy & Security → Automation
- Enable OmniFocus for Terminal

**Full Disk Access (Database queries):**

- System Settings → Privacy & Security → Full Disk Access
- Add Terminal app

**Restart terminal after granting permissions.**

### Common Errors

- **"Not authorized"** → Grant automation permission
- **"Database not found"** → Grant Full Disk Access
- **"Multiple tasks found"** → Use task ID instead of name
- **"Invalid date"** → Use ISO 8601 format: `YYYY-MM-DD`

**See:** [Troubleshooting Guide](references/troubleshooting.md)

---

## Version Information

**Current version:** 3.1.0

**What's new in 3.1:**

- ⭐ Official plugin template reference (OFBundlePlugInTemplate)
- ⭐ Comprehensive plugin testing workflows
- ⭐ Plugin distribution checklist
- Expanded plugin development guide with OFBundlePlugInTemplate patterns
- Detailed Automation Console testing procedures
- Plugin validation and testing best practices

**What's new in 3.0:**

- ⭐ Modular library system (`scripts/libraries/`)
- ⭐ Execution-first architecture (80/15/5 split)
- ⭐ Comprehensive examples (`assets/examples/`)
- ⭐ Progressive disclosure documentation
- ⭐ Quickstart guides (5-minute tutorials)
- Foundation Models integration (OmniFocus 4.8+)
- Merged documentation (reduced overlap)
- GTD navigation hub

**Migration from 2.x:** Major architectural refactoring. Documentation reorganized, libraries modularized. Existing generated scripts continue to work. New modular libraries and examples available for composition.

---

## External Resources

- **Omni Automation:** [omni-automation.com/omnifocus](https://omni-automation.com/omnifocus/)
- **OmniFocus URL Schemes:** [support.omnigroup.com/omnifocus-url-schemes](https://support.omnigroup.com/omnifocus-url-schemes/)
- **OmniFocus AppleScript:** [support.omnigroup.com/omnifocus-applescript](https://support.omnigroup.com/omnifocus-applescript/)
- **OmniFocus Manual:** [support.omnigroup.com/documentation/omnifocus/](https://support.omnigroup.com/documentation/omnifocus/)
- **GTD Methodology:** [gettingthingsdone.com](https://gettingthingsdone.com)
