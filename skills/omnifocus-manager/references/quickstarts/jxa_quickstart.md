# JXA Quickstart: Automate OmniFocus from the Command Line

Get started with JavaScript for Automation (JXA) to automate OmniFocus from scripts and terminal.

## What You'll Build

A command-line script that shows today's tasks. You'll learn:
- JXA basics for OmniFocus
- Loading and using libraries
- Running scripts from terminal

**Time:** 5 minutes
**Difficulty:** Beginner
**Platform:** macOS only

---

## Prerequisites

- macOS with OmniFocus installed
- Text editor
- Terminal access
- Basic JavaScript knowledge (helpful but not required)

---

## Quick Start: Use Existing Scripts

**Fastest way to get started:**

```bash
# Navigate to skill directory
cd /path/to/omnifocus-manager

# Run example script
osascript -l JavaScript assets/examples/standalone/query-today.js
```

**That's it!** You just queried OmniFocus from the command line.

---

## Step 1: Your First Script (2 min)

Create a file `today.js`:

```javascript
#!/usr/bin/osascript -l JavaScript

// This makes it an executable script

ObjC.import('Foundation');

function run(argv) {
    // Get OmniFocus application
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Get today's tasks
    const tasks = doc.flattenedTasks();
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const todayTasks = tasks.filter(task => {
        if (task.completed() || task.dropped()) return false;

        const due = task.dueDate();
        const defer = task.deferDate();

        return (due && due >= now && due < tomorrow) ||
               (defer && defer >= now && defer < tomorrow);
    });

    // Display results
    console.log(`\nYou have ${todayTasks.length} tasks today:\n`);

    todayTasks.forEach((task, index) => {
        console.log(`${index + 1}. ${task.name()}`);
    });

    console.log('');
}
```

**Run it:**
```bash
chmod +x today.js
./today.js
```

**Output:**
```
You have 5 tasks today:

1. Call dentist
2. Review proposal
3. Team meeting
4. Update documentation
5. Weekly review
```

---

## Step 2: Use Libraries for Easier Code (2 min)

Instead of writing query logic yourself, use the taskQuery library:

Create `today-with-library.js`:

```javascript
#!/usr/bin/osascript -l JavaScript

ObjC.import('Foundation');

// Helper to load library
function loadLibrary(path) {
    return eval($.NSString.alloc.initWithContentsOfFileEncodingError(
        path, $.NSUTF8StringEncoding, null
    ).js);
}

function run(argv) {
    // Load taskQuery library
    const taskQuery = loadLibrary('libraries/jxa/taskQuery.js');

    // Get OmniFocus document
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Query today's tasks (one line!)
    const tasks = taskQuery.getTodayTasks(doc);

    // Display results
    console.log(`\nYou have ${tasks.length} tasks today:\n`);

    tasks.forEach((task, index) => {
        console.log(`${index + 1}. ${task.name}`);
        if (task.project) {
            console.log(`   Project: ${task.project}`);
        }
    });

    console.log('');
}
```

**Much simpler!** The library handles all the date logic and filtering.

**Run it:**
```bash
./today-with-library.js
```

---

## Step 3: Add Command-Line Arguments (1 min)

Make your script more flexible:

```javascript
#!/usr/bin/osascript -l JavaScript

ObjC.import('Foundation');

function loadLibrary(path) {
    return eval($.NSString.alloc.initWithContentsOfFileEncodingError(
        path, $.NSUTF8StringEncoding, null
    ).js);
}

function run(argv) {
    const taskQuery = loadLibrary('libraries/jxa/taskQuery.js');
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Parse arguments
    const filter = argv[0] || 'today';

    let tasks;
    if (filter === 'today') {
        tasks = taskQuery.getTodayTasks(doc);
    } else if (filter === 'overdue') {
        tasks = taskQuery.getOverdueTasks(doc);
    } else if (filter === 'flagged') {
        tasks = taskQuery.getFlagged(doc);
    } else {
        console.log('Usage: ./script.js [today|overdue|flagged]');
        return;
    }

    // Display results
    console.log(`\n${filter.toUpperCase()}: ${tasks.length} tasks\n`);

    tasks.forEach((task, index) => {
        console.log(`${index + 1}. ${task.name}`);
    });

    console.log('');
}
```

**Usage:**
```bash
./script.js today
./script.js overdue
./script.js flagged
```

---

## What You Just Learned

✅ JXA script structure (`#!/usr/bin/osascript -l JavaScript`)
✅ Accessing OmniFocus via Application API
✅ Loading and using libraries
✅ Processing command-line arguments
✅ Querying tasks with filters

---

## Available Libraries

### taskQuery.js - Query Operations

```javascript
const taskQuery = loadLibrary('libraries/jxa/taskQuery.js');

taskQuery.getTodayTasks(doc);           // Tasks due/deferred today
taskQuery.getOverdueTasks(doc);         // Past due tasks
taskQuery.getDueSoon(doc, 7);           // Due within 7 days
taskQuery.getFlagged(doc);              // Flagged tasks
taskQuery.searchTasks(doc, "meeting");  // Search by name/note
taskQuery.formatTaskInfo(task);         // Normalize task data
```

### taskMutation.js - Create/Update/Delete

```javascript
const taskMutation = loadLibrary('libraries/jxa/taskMutation.js');

// Create task
taskMutation.createTask(app, doc, {
    name: "Call dentist",
    project: "Health",
    tags: "phone,urgent",
    due: new Date("2025-12-30"),
    flagged: true,
    createProject: true,
    createTags: true
});

// Update task
taskMutation.updateTask(app, doc, "Task name", {
    flagged: true,
    due: new Date("2025-12-31")
});

// Complete task
taskMutation.completeTask(doc, "Task name");
```

### dateUtils.js - Date Helpers

```javascript
const dateUtils = loadLibrary('libraries/jxa/dateUtils.js');

dateUtils.parseDate("2025-12-30");        // Parse ISO date
dateUtils.parseEstimate("1h30m");         // Returns 90 (minutes)
dateUtils.formatDate(new Date());         // ISO string
dateUtils.isToday(task.dueDate());        // Boolean
```

### argParser.js - CLI Arguments

```javascript
const argParser = loadLibrary('libraries/jxa/argParser.js');

const args = argParser.parseArgs(argv);
// argv: ["create", "--name", "Task", "--flagged"]
// args: { action: "create", name: "Task", flagged: true }

argParser.printHelp();  // Shows usage information
```

---

## Common Patterns

### Create a Task

```javascript
const app = Application('OmniFocus');
const doc = app.defaultDocument;
const taskMutation = loadLibrary('libraries/jxa/taskMutation.js');

const result = taskMutation.createTask(app, doc, {
    name: "Buy groceries",
    tags: "errands",
    flagged: true,
    createTags: true
});

console.log(`Created: ${result.name} (ID: ${result.id})`);
```

### Export to JSON

```javascript
const tasks = taskQuery.getTodayTasks(doc);

// Print JSON
console.log(JSON.stringify(tasks, null, 2));

// Or save to file
const json = JSON.stringify(tasks, null, 2);
const path = $.NSString.alloc.initWithUTF8String("tasks.json");
const data = $.NSString.alloc.initWithUTF8String(json);
data.writeToFileAtomicallyEncodingError(path, true, $.NSUTF8StringEncoding, null);
```

### Weekly Review Report

```javascript
const today = taskQuery.getTodayTasks(doc);
const overdue = taskQuery.getOverdueTasks(doc);
const dueSoon = taskQuery.getDueSoon(doc, 7);

console.log('\n=== WEEKLY REVIEW ===\n');
console.log(`Today: ${today.length} tasks`);
console.log(`Overdue: ${overdue.length} tasks`);
console.log(`This week: ${dueSoon.length} tasks\n`);

if (overdue.length > 0) {
    console.log('⚠️  OVERDUE TASKS:');
    overdue.forEach(t => console.log(`  - ${t.name}`));
}
```

---

## Complete Examples

The skill includes 4 complete JXA script examples:

### check-today.js
Full-featured daily task report with priority ranking.

**Features:**
- Groups tasks by project
- Highlights overdue items
- Shows flagged tasks
- Provides actionable next steps

**Location:** `assets/examples/jxa-scripts/check-today.js`

### bulk-create.js
Create multiple tasks from templates.

**Features:**
- Built-in template library
- Batch task creation
- Error handling
- Summary reporting

**Location:** `assets/examples/jxa-scripts/bulk-create.js`

### weekly-review.js
Complete GTD weekly review with analysis.

**Features:**
- Analyzes all projects
- Detects stalled items
- Generates recommendations
- JSON or text output

**Location:** `assets/examples/jxa-scripts/weekly-review.js`

### generate-report.js
Export tasks to various formats.

**Features:**
- Multiple filters (today, overdue, flagged, week)
- Multiple formats (JSON, CSV, Markdown)
- File or console output

**Location:** `assets/examples/jxa-scripts/generate-report.js`

---

## Automation Ideas

### Cron Job: Daily Summary

Add to crontab to run every morning:
```bash
0 8 * * * /path/to/check-today.js > ~/today.txt
```

### Alfred Workflow

Create Alfred workflow that runs:
```bash
osascript -l JavaScript check-today.js
```

### Shell Alias

Add to `.zshrc` or `.bashrc`:
```bash
alias oft='osascript -l JavaScript ~/scripts/today.js'
alias ofo='osascript -l JavaScript ~/scripts/today.js overdue'
alias off='osascript -l JavaScript ~/scripts/today.js flagged'
```

Usage: Just type `oft` to see today's tasks!

### Git Hook: Pre-Commit

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
osascript -l JavaScript ~/scripts/check-today.js
read -p "Press enter to continue commit..."
```

Shows your tasks before each commit.

---

## Troubleshooting

**"Application isn't running" error:**
- OmniFocus must be running (open it first)
- Or use: `const app = Application('OmniFocus'); app.activate();`

**Library not found:**
- Check path is correct (relative or absolute)
- Use absolute paths for cron jobs: `/full/path/to/library.js`

**Permission denied:**
- Make script executable: `chmod +x script.js`
- Grant Terminal accessibility permissions in System Settings

**Dates showing wrong timezone:**
- JXA dates are in local timezone
- Use `.toISOString()` for UTC: `task.dueDate().toISOString()`

---

## Going Further

### URL Scheme Integration

Combine JXA with URL schemes:

```javascript
const urlBuilder = loadLibrary('libraries/shared/urlBuilder.js');

// Generate URL for external apps
const url = urlBuilder.buildTaskURL({
    name: "Call client",
    project: "Work",
    tags: ["phone", "urgent"],
    flagged: true
});

// Open URL in browser (creates task when clicked)
const browser = Application('Safari');
browser.openLocation(url);
```

### Database Queries (Advanced)

For complex queries, use SQLite directly:

```javascript
// See scripts/query_omnifocus.py for examples
// SQLite database: ~/Library/Group Containers/.../OmniFocus.ofocus/
```

### Combine with Other Tools

**Export to Obsidian:**
```javascript
const tasks = taskQuery.getTodayTasks(doc);
const markdown = formatAsMarkdown(tasks);
// Write to Obsidian vault
```

**Send to Things 3:**
```javascript
const tasks = taskQuery.getOverdueTasks(doc);
// Convert to Things JSON import format
```

---

## Resources

### Documentation
- **JXA API Guide:** `../jxa_api_guide.md` (complete reference)
- **Library Documentation:** `../../libraries/README.md`
- **Example Scripts:** `../../assets/examples/jxa-scripts/`
- **OmniFocus API:** `../OmniFocus-API.md`

### External Resources
- [JXA Cookbook](https://github.com/JXA-Cookbook/JXA-Cookbook)
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [OmniFocus AppleScript Reference](https://support.omnigroup.com/omnifocus-applescript-reference/)

---

## What's Next?

**Beginner:**
- Run the example scripts in `assets/examples/jxa-scripts/`
- Modify them for your workflows
- Create daily automation routines

**Intermediate:**
- Combine multiple libraries
- Export to different formats
- Integrate with other apps

**Advanced:**
- Direct SQLite database queries
- Create complex workflows
- Build command-line tools

**Ready for plugins?** See the [Plugin Quickstart](plugin_quickstart.md) to create OmniFocus UI actions.
