# OmniFocus Libraries

Modular, composable libraries for OmniFocus automation with MCP-ready interfaces.

## Overview

This directory contains reusable libraries organized by environment and use case:

```
libraries/
├── jxa/                 # JXA-specific libraries (macOS only)
├── omni/                # Omni Automation libraries (cross-platform: Mac + iOS)
├── shared/              # Cross-platform utilities (JXA + Omni Automation)
└── README.md            # This file
```

**Philosophy: Execute > Generate**
- These libraries enable **execution-first architecture**
- 80% of use cases: Execute existing code with parameters
- 15% of use cases: Compose existing patterns
- 5% of use cases: Generate new code

**MCP-Ready Interfaces**
- All functions use clean JSON input/output contracts
- Designed to become MCP (Model Context Protocol) tools
- Future: Each library function becomes a callable tool in MCP servers

---

## Library Categories

### JXA Libraries (`libraries/jxa/`)

**Environment:** macOS only (JavaScript for Automation)
**Use Cases:** CLI scripts, standalone automation, database queries

| Library | Description | Lines | Key Functions |
|---------|-------------|-------|---------------|
| `taskQuery.js` | Query operations | 271 | getTodayTasks, getDueSoon, getFlagged, searchTasks, getOverdueTasks |
| `taskMutation.js` | CRUD operations | 384 | createTask, updateTask, completeTask, deleteTask, findOrCreateProject |
| `dateUtils.js` | Date utilities | 99 | parseDate, parseEstimate, formatDate, isToday, isBetween |
| `argParser.js` | CLI argument parsing | 161 | parseArgs, parseOption, printHelp |

**Usage Pattern:**
```javascript
// Load library via Foundation framework
ObjC.import('Foundation');
const taskQuery = eval($.NSString.alloc.initWithContentsOfFileEncodingError(
    'libraries/jxa/taskQuery.js', $.NSUTF8StringEncoding, null
).js);

// Use functions
const app = Application('OmniFocus');
const doc = app.defaultDocument;
const tasks = taskQuery.getTodayTasks(doc);
```

### Omni Automation Libraries (`libraries/omni/`)

**Environment:** Cross-platform (macOS + iOS/iPadOS)
**Use Cases:** OmniFocus plugins, Omni Automation console

All libraries use `PlugIn.Library` pattern for reusability across plugins.

| Library | Description | Lines | Key Functions |
|---------|-------------|-------|---------------|
| **`patterns.js` ⭐** | **Composable patterns (MCP-ready)** | **~600** | **queryAndAnalyzeWithAI, queryAndExport, batchUpdate, periodicReview, detectPatterns** |
| `taskMetrics.js` | Task data collection | 281 | getTodayTasks, getOverdueTasks, getFlaggedTasks, getSummaryStats, normalizeTask |
| `exportUtils.js` | Export to formats | 338 | toClipboard, toFile, toJSON, toCSV, toMarkdown, toHTML |
| `insightPatterns.js` | Pattern detection | ~400 | detectStalledProjects, detectWaitingForAging, generateInsights, formatReport |
| `templateEngine.js` | Template system | ~350 | loadTemplates, createFromTemplate, substituteVariables, listTemplates |

**Usage Pattern (in OmniFocus plugin):**
```javascript
// In manifest.json:
{
  "libraries": ["patterns", "taskMetrics", "exportUtils"]
}

// In action script:
const patterns = this.plugIn.library("patterns");
const result = await patterns.queryAndAnalyzeWithAI({
  query: { filter: "today" },
  patterns: ["stalled", "overdue"]
});
```

**Usage Pattern (in Omni Automation console):**
```javascript
// Load library code (paste library file contents)
const patterns = <library code>;

// Use functions
const result = await patterns.queryAndAnalyzeWithAI({...});
```

### Shared Libraries (`libraries/shared/`)

**Environment:** Cross-platform (JXA + Omni Automation)
**Use Cases:** URL building, common utilities

| Library | Description | Lines | Key Functions |
|---------|-------------|-------|---------------|
| `urlBuilder.js` | OmniFocus URL scheme | ~400 | buildTaskURL, buildPerspectiveURL, buildMarkdownLink, parseURL |

**Usage Pattern:**
```javascript
// Works in both JXA and Omni Automation
const urlBuilder = <load library>;

const url = urlBuilder.buildTaskURL({
  name: "Call dentist",
  tags: ["phone", "health"],
  due: "2025-12-30T14:00:00",
  flagged: true
});
// Returns: omnifocus:///add?name=Call%20dentist&tags=phone%2Chealth&due=2025-12-30T14%3A00%3A00&flagged=true
```

---

## Patterns Library: MCP-Ready Functions ⭐

The **patterns.js** library is the PRIMARY new capability with Foundation Models integration.

### Core Pattern Functions

Each function has a clean JSON contract designed for MCP tool definitions:

#### 1. queryAndAnalyzeWithAI()

**Purpose:** Query tasks and analyze with AI-powered insights

**Input Contract:**
```javascript
{
  query: {
    filter: "today" | "overdue" | "flagged" | "available" | "tag" | "project",
    tagName: "optional-tag-name",     // when filter="tag"
    projectName: "optional-project",   // when filter="project"
    days: 7                            // when filter="upcoming"
  },
  prompt: "Analysis prompt for AI",    // Future: Foundation Models
  schema: { /* expected response */ }, // Future: Structured output
  patterns: ["stalled", "overdue"]     // Patterns to detect (optional)
}
```

**Output Contract:**
```javascript
{
  success: true,
  tasks: [{name, project, tags, dueDate, ...}],
  analysis: {
    summary: {total, blockers, health, opportunities, healthScore},
    insights: [{category, severity, pattern, title, details, recommendation}]
  },
  recommendations: [{priority, action, reason}],
  metadata: {duration, taskCount, insightCount, version}
}
```

**Future:** When Apple Foundation Models API becomes available, this function will call on-device AI for nuanced analysis instead of rule-based patterns.

#### 2. queryAndExport()

**Purpose:** Query tasks, optionally transform, and export to format/destination

**Input Contract:**
```javascript
{
  query: { /* same as queryAndAnalyzeWithAI */ },
  transform: "summary" | "detailed" | "custom",
  export: {
    format: "json" | "csv" | "markdown" | "html",
    destination: "clipboard" | "file",
    filename: "optional-filename.ext",
    title: "Optional Title for Markdown"
  }
}
```

**Output Contract:**
```javascript
{
  success: true,
  count: 12,
  destination: "clipboard" | "filename.ext",
  format: "json",
  preview: "First 200 chars of exported data...",
  metadata: {duration, version}
}
```

#### 3. batchUpdate()

**Purpose:** Batch update tasks matching selector

**Input Contract:**
```javascript
{
  selector: { /* same query structure */ },
  updates: {
    flagged: true,
    tag: "new-tag",
    project: "target-project",
    defer: "2025-12-30"
  },
  dryRun: true  // Default: true for safety
}
```

**Output Contract:**
```javascript
{
  success: true,
  matched: 15,
  updated: 15,  // 0 if dryRun=true
  dryRun: true,
  changes: [{task, before, after}],
  errors: [{task, error}],
  metadata: {duration, version}
}
```

#### 4. periodicReview()

**Purpose:** Perform periodic review (daily, weekly, monthly)

**Input Contract:**
```javascript
{
  period: "daily" | "weekly" | "monthly",
  focus: "inbox" | "projects" | "waiting" | "all"
}
```

**Output Contract:**
```javascript
{
  success: true,
  tasks: {
    overdue: [...],
    today: [...],
    upcoming: [...],
    flagged: [...]
  },
  insights: { /* same as queryAndAnalyzeWithAI */ },
  actions: [{action, reason, tasks}],
  metadata: {duration, period, totalTasks, version}
}
```

#### 5. detectPatterns()

**Purpose:** Detect specific patterns in task data

**Input Contract:**
```javascript
{
  patterns: ["stalled", "over-committed", "aging-waiting", "inbox-overflow", "tagless", "flag-overuse"],
  threshold: { /* custom thresholds */ }
}
```

**Output Contract:**
```javascript
{
  success: true,
  detected: [{category, severity, pattern, title, details, recommendation}],
  summary: {total, blockers, health, opportunities, healthScore},
  metadata: {duration, patternsRequested, patternsDetected, version}
}
```

---

## MCP Roadmap

**Goal:** Convert library functions into MCP (Model Context Protocol) server tools

### Phase 1: Design Interfaces ✅ (Complete)
- [x] Define JSON input/output contracts for all functions
- [x] Document contracts in JSDoc format
- [x] Create MCP-ready patterns library
- [x] Design for future Foundation Models integration

### Phase 2: MCP Server Implementation (Future)
- [ ] Create MCP server using Anthropic MCP SDK
- [ ] Map each pattern function to MCP tool definition
- [ ] Implement server transport (stdio or HTTP)
- [ ] Add authentication and security

### Phase 3: Integration (Future)
- [ ] Connect MCP server to Claude Desktop
- [ ] Enable skill to call local MCP tools
- [ ] Reduce token usage (execute local vs generate code)
- [ ] Add Foundation Models when API available

**Example MCP Tool Definition (Future):**
```typescript
{
  name: "omnifocus_query_and_analyze",
  description: "Query OmniFocus tasks and analyze patterns",
  inputSchema: {
    type: "object",
    properties: {
      query: { /* schema from patterns.js */ },
      patterns: { /* ... */ }
    }
  },
  handler: async (input) => {
    // Call patterns.queryAndAnalyzeWithAI()
    return result;
  }
}
```

---

## Usage Examples

### Standalone Script (JXA)

```javascript
#!/usr/bin/osascript -l JavaScript

ObjC.import('Foundation');

// Load libraries
function loadLibrary(path) {
    return eval($.NSString.alloc.initWithContentsOfFileEncodingError(
        path, $.NSUTF8StringEncoding, null
    ).js);
}

const taskQuery = loadLibrary('libraries/jxa/taskQuery.js');
const dateUtils = loadLibrary('libraries/jxa/dateUtils.js');

function run(argv) {
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Get today's tasks
    const tasks = taskQuery.getTodayTasks(doc);

    console.log(`You have ${tasks.length} tasks today:`);
    tasks.forEach(t => {
        const due = t.dueDate ? dateUtils.formatDate(t.dueDate) : 'No due date';
        console.log(`- ${t.name} (${due})`);
    });
}
```

### OmniFocus Plugin (Omni Automation)

**manifest.json:**
```json
{
  "identifier": "com.example.task-analyzer",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Analyze tasks with insights",
  "label": "Task Analyzer",
  "libraries": ["patterns", "taskMetrics", "exportUtils", "insightPatterns"],
  "actions": [
    {
      "identifier": "analyzeToday",
      "label": "Analyze Today's Tasks",
      "mediumLabel": "Analyze Today",
      "shortLabel": "Analyze"
    }
  ]
}
```

**Resources/analyzeToday.js:**
```javascript
(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // Load patterns library
        const patterns = this.plugIn.library("patterns");

        // Analyze today's tasks
        const result = await patterns.queryAndAnalyzeWithAI({
            query: { filter: "today" }
        });

        // Display insights
        const insights = this.plugIn.library("insightPatterns");
        const report = insights.formatReport(result.analysis);

        new Alert("Today's Task Analysis", report).show();
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
```

### Skill Execution (Primary Use Case)

The omnifocus-manager skill uses these libraries to EXECUTE automation instead of generating code:

**Low-cost execution (most common):**
```
User: "Show me today's tasks"
Skill: Executes → osascript scripts/omnifocus.js query --filter today
      Returns → JSON → Presents to user
```

**Medium-cost composition:**
```
User: "Export my flagged tasks to markdown"
Skill: Executes → patterns.queryAndExport({
         query: {filter: "flagged"},
         export: {format: "markdown", destination: "clipboard"}
       })
```

**High-cost generation (rare):**
```
User: "Create a plugin that does X"
Skill: Generates → New plugin using library patterns
      Offers → "Should I add this to my repertoire?"
```

---

## Library Dependencies

### External Dependencies
- **JXA libraries:** Require macOS, OmniFocus installed
- **Omni libraries:** Require OmniFocus (Mac or iOS)
- **Shared libraries:** No dependencies (pure JavaScript)

### Internal Dependencies

```
patterns.js
├── taskMetrics.js (data collection)
├── exportUtils.js (export functionality)
└── insightPatterns.js (pattern detection)

insightPatterns.js
└── <no dependencies>

templateEngine.js
└── <no dependencies>

taskMetrics.js
└── <no dependencies>

exportUtils.js
└── <no dependencies>

urlBuilder.js
└── <no dependencies>
```

**Loading Order (in plugins):**
```json
{
  "libraries": [
    "taskMetrics",
    "exportUtils",
    "insightPatterns",
    "templateEngine",
    "patterns"
  ]
}
```

---

## Version History

### v3.0.0 (2025-12-30)
- Complete library modularization
- Added patterns.js with MCP-ready interfaces ⭐
- Foundation Models integration design (implementation pending API)
- Execution-first architecture
- PlugIn.Library pattern for all Omni libraries
- Cross-platform shared utilities

### v2.2.x (Previous)
- Plugin-specific libraries (taskMetrics, exportUtils)
- Monolithic scripts (manage_omnifocus.js)

### v1.x (Legacy)
- Single-file scripts
- No library structure

---

## Contributing

When adding new library functions:

1. **Design MCP-ready interfaces:**
   - JSON input parameters (no code, just config)
   - JSON output results (structured, documented)
   - Error objects with standard format

2. **Document contracts:**
   - JSDoc comments with param types
   - Input/output examples
   - Error scenarios

3. **Follow patterns:**
   - JXA: IIFE returning object with functions
   - Omni: PlugIn.Library wrapper
   - Shared: Cross-platform compatible

4. **Consider promotion:**
   - Novel generated code → Should it become a library function?
   - Reusable across use cases → Add to library
   - User-specific logic → Keep as one-time generation

---

## Resources

**Skill References:**
- `../references/omnifocus_automation.md` - OmniFocus Omni Automation API
- `../references/jxa_commands.md` - JXA command reference
- `../references/omnifocus_url_scheme.md` - URL scheme documentation
- `../references/foundation_models_integration.md` - Apple Intelligence integration (future)

**External Documentation:**
- Omni Automation: [omni-automation.com/omnifocus](https://omni-automation.com/omnifocus/)
- JXA Guide: [developer.apple.com](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- MCP Specification: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- Anthropic MCP SDK: [github.com/anthropics/anthropic-sdk-typescript](https://github.com/anthropics/anthropic-sdk-typescript)

---

## License

Part of the omnifocus-manager skill. See parent directory for license information.
