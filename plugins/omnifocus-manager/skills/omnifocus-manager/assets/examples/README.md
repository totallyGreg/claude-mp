# OmniFocus Library Usage Examples

Complete, runnable examples demonstrating the three usage patterns for OmniFocus libraries.

## Quick Reference

| Example Type | Use Case | Environment | Complexity |
|--------------|----------|-------------|------------|
| **Standalone** | Learn individual library functions | macOS (JXA) | Beginner |
| **JXA Scripts** | Complete automation workflows | macOS (JXA) | Intermediate |
| **Plugins** | Reusable OmniFocus actions | Mac + iOS (Omni Automation) | Advanced |

---

## Standalone Examples (`standalone/`)

**Purpose:** Learn how to load and use individual library functions

These examples show the minimal code needed to use a single library. Perfect for:
- Understanding library APIs
- Quick prototyping
- Learning JXA basics

### query-today.js
Load and use `taskQuery` library to get today's tasks.

**Usage:**
```bash
osascript -l JavaScript standalone/query-today.js
```

**Demonstrates:**
- Loading JXA library via Foundation framework
- Calling taskQuery.getTodayTasks()
- Displaying results

### create-task.js
Load and use `taskMutation` library to create a task.

**Usage:**
```bash
osascript -l JavaScript standalone/create-task.js "Task name" --project "Work" --tags "urgent"
```

**Demonstrates:**
- Loading multiple libraries (taskMutation + dateUtils)
- Parsing command-line arguments
- Creating tasks with options

### build-url.js
Load and use `urlBuilder` library to generate OmniFocus URLs.

**Usage:**
```bash
osascript -l JavaScript standalone/build-url.js "Call dentist" --tags "phone,health" --flagged
```

**Demonstrates:**
- Loading shared library (cross-platform)
- Building omnifocus:// URLs
- URL validation
- Generating markdown links

---

## Complete JXA Scripts (`jxa-scripts/`)

**Purpose:** Real-world automation workflows combining multiple libraries

These are production-ready scripts that solve actual problems. Perfect for:
- Daily automation
- Weekly reviews
- Report generation
- Task management workflows

### check-today.js
Comprehensive daily task report with priority ranking.

**Usage:**
```bash
chmod +x jxa-scripts/check-today.js
./jxa-scripts/check-today.js
```

**Features:**
- Shows today's tasks grouped by project
- Highlights overdue tasks
- Displays flagged items
- Provides actionable next steps

**Demonstrates:**
- Loading multiple libraries
- Querying different task categories
- Grouping and formatting results
- Returning structured JSON

### bulk-create.js
Create multiple tasks from templates or lists.

**Usage:**
```bash
./jxa-scripts/bulk-create.js --template "weekly-review"
./jxa-scripts/bulk-create.js --template "meeting-prep" --project "Work"
```

**Features:**
- Built-in template library
- Batch task creation
- Error handling
- Summary reporting

**Demonstrates:**
- Template-based workflows
- Batch operations
- Error collection
- Argument parsing

### weekly-review.js
Complete GTD weekly review with project analysis.

**Usage:**
```bash
./jxa-scripts/weekly-review.js
./jxa-scripts/weekly-review.js --format json > review.json
```

**Features:**
- Analyzes all projects for stalled items
- Detects overdue accumulation
- Checks inbox size
- Generates recommendations
- Outputs text or JSON

**Demonstrates:**
- Complex data analysis
- Pattern detection
- Recommendation generation
- Multiple output formats

### generate-report.js
Export tasks to various formats (JSON, CSV, Markdown).

**Usage:**
```bash
./jxa-scripts/generate-report.js --filter today --format markdown
./jxa-scripts/generate-report.js --filter overdue --format csv --output overdue.csv
```

**Features:**
- Multiple query filters (today, overdue, flagged, week)
- Multiple formats (JSON, CSV, Markdown)
- File or console output
- Formatted reports

**Demonstrates:**
- Query + export workflow
- Format conversion
- File I/O
- Flexible command-line interface

---

## OmniFocus Plugins (`plugins/`)

**Purpose:** Reusable actions that integrate into OmniFocus UI

These are complete plugin bundles ready to install. Perfect for:
- Frequently-used operations
- Actions available from OmniFocus menu
- Cross-platform automation (Mac + iOS)

### SimpleQuery.omnifocusjs
Basic query plugin using `taskMetrics` and `exportUtils` libraries.

**Install:**
1. Double-click `SimpleQuery.omnifocusjs` to install
2. Or copy to: `~/Library/Group Containers/.../OmniFocus/Plug-Ins/`

**Actions:**
- **Show Today's Tasks:** Display today's tasks grouped by project
- **Show Flagged Tasks:** List all flagged items
- **Export Today to Markdown:** Export today's tasks to clipboard as Markdown

**Demonstrates:**
- Loading PlugIn.Library modules
- Using taskMetrics for queries
- Using exportUtils for export
- Alert dialogs

**Structure:**
```
SimpleQuery.omnifocusjs/
├── manifest.json               # Plugin metadata + library declarations
└── Resources/
    ├── queryToday.js           # Action: Show today's tasks
    ├── queryFlagged.js         # Action: Show flagged tasks
    └── exportToMarkdown.js     # Action: Export to markdown
```

### BulkOperations.omnifocusjs
Advanced batch operations using `patterns` library.

**Install:** Double-click to install

**Actions:**
- **Flag All Overdue Tasks:** Batch flag overdue items (with dry-run preview)
- **Export Project Tasks:** Export tasks from selected project

**Demonstrates:**
- Using patterns library for batch operations
- Dry-run preview before execution
- Form prompts for user input
- Query + export composition

**Structure:**
```
BulkOperations.omnifocusjs/
├── manifest.json               # Declares patterns + dependencies
└── Resources/
    ├── flagAllOverdue.js       # Batch operation with preview
    └── exportByProject.js      # Project export workflow
```

### URLGenerator.omnifocusjs
URL generation for task sharing using `urlBuilder` library.

**Install:** Double-click to install

**Actions:**
- **Generate Task URL from Selection:** Create omnifocus:// URL for selected task
- **Generate Quick Entry URL:** Form-based URL generator

**Demonstrates:**
- Loading shared library in Omni Automation
- Building omnifocus:// URLs
- Clipboard operations
- Form-based data entry

**Structure:**
```
URLGenerator.omnifocusjs/
├── manifest.json               # Plugin metadata
└── Resources/
    ├── generateTaskURL.js      # Generate from selection
    └── generateQuickEntry.js   # Form-based generator
```

---

## Usage Patterns

### Pattern 1: Standalone Library Loading

```javascript
ObjC.import('Foundation');

// Load library
const taskQuery = eval($.NSString.alloc.initWithContentsOfFileEncodingError(
    'path/to/taskQuery.js', $.NSUTF8StringEncoding, null
).js);

// Use library
const app = Application('OmniFocus');
const tasks = taskQuery.getTodayTasks(app.defaultDocument);
```

### Pattern 2: Complete JXA Script

```javascript
#!/usr/bin/osascript -l JavaScript

ObjC.import('Foundation');

// Helper to load libraries
function loadLibrary(filename) {
    const path = '../../libraries/jxa/' + filename;
    return eval($.NSString.alloc.initWithContentsOfFileEncodingError(
        path, $.NSUTF8StringEncoding, null
    ).js);
}

// Load multiple libraries
const taskQuery = loadLibrary('taskQuery.js');
const dateUtils = loadLibrary('dateUtils.js');

function run(argv) {
    // Your automation logic here
}
```

### Pattern 3: OmniFocus Plugin

**manifest.json:**
```json
{
  "identifier": "com.example.my-plugin",
  "version": "1.0.0",
  "libraries": ["taskMetrics", "exportUtils"],
  "actions": [...]
}
```

**Resources/action.js:**
```javascript
(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // Load library declared in manifest
        const metrics = this.plugIn.library("taskMetrics");

        // Use library
        const tasks = metrics.getTodayTasks();

        // Display results
        const alert = new Alert("Results", `Found ${tasks.length} tasks`);
        await alert.show();
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
```

---

## Library Paths

When loading libraries in examples:

**Standalone Examples:** Use absolute paths
```javascript
const path = '/full/path/to/libraries/jxa/taskQuery.js';
```

**JXA Scripts:** Use relative paths from script location
```javascript
const scriptDir = $.NSString.alloc.initWithUTF8String($.getenv('_')).stringByDeletingLastPathComponent;
const libPath = scriptDir.stringByAppendingPathComponent('../../libraries/jxa/taskQuery.js');
```

**Plugins:** Declare in manifest.json
```json
{
  "libraries": ["taskMetrics", "exportUtils", "patterns"]
}
```

---

## Modifying Examples

All examples are fully editable. To customize:

1. **Standalone/JXA:** Edit .js files directly
2. **Plugins:**
   - Right-click `.omnifocusjs` bundle
   - Select "Show Package Contents"
   - Edit `manifest.json` or `Resources/*.js` files
   - Restart OmniFocus to reload

---

## Creating Your Own

Use these examples as templates:

1. **Start with standalone** to learn a library
2. **Move to JXA scripts** for complete workflows
3. **Create plugins** for frequently-used actions

**Tip:** Copy an example, modify for your needs, test, then optionally promote to your personal plugin library.

---

## Next Steps

- **Learn libraries:** See `../../libraries/README.md`
- **API references:** See `../../references/` directory
- **Quickstart guides:** See `../../references/quickstarts/`
- **Plugin development:** See `../../references/plugin_development_guide.md`

---

## Resources

- **Library Documentation:** `libraries/README.md`
- **OmniFocus API:** `references/OmniFocus-API.md`
- **JXA Guide:** `references/jxa_api_guide.md`
- **Plugin Guide:** `references/plugin_development_guide.md`
- **URL Scheme:** `references/omnifocus_url_scheme.md`
