# JXA API Guide

Complete guide to JavaScript for Automation (JXA) with OmniFocus - from quick scripts to modular library usage.

**New to JXA?** Start with the [JXA Quickstart Guide](quickstarts/jxa_quickstart.md) for a 5-minute introduction.

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Using Modular Libraries](#using-modular-libraries)
4. [AppleScript API Reference](#applescript-api-reference)
5. [CLI Command Reference](#cli-command-reference)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Resources](#resources)

---

## Overview

### What is JXA?

**JavaScript for Automation (JXA)** is Apple's JavaScript interface to the AppleScript API. It allows you to automate macOS applications using JavaScript instead of AppleScript.

**Key characteristics:**
- **macOS only** - Uses AppleScript bridge (not available on iOS)
- **External scripts** - Runs from command line or as standalone scripts
- **Full API access** - Complete access to OmniFocus AppleScript API
- **Method call syntax** - Properties accessed via methods: `task.name()`

### When to Use JXA

**Use JXA when:**
- ✅ Automating from command line or external tools
- ✅ Integrating OmniFocus with other macOS apps
- ✅ Creating scheduled automation (cron jobs, Alfred workflows)
- ✅ Mac-only automation is acceptable
- ✅ You prefer JavaScript over AppleScript

**Use Omni Automation when:**
- ✅ Need cross-platform support (Mac + iOS)
- ✅ Creating plugins that integrate into OmniFocus UI
- ✅ Want actions available from OmniFocus menu
- ✅ Prefer direct property access: `task.name`

### JXA vs Omni Automation

| Feature | JXA (AppleScript API) | Omni Automation |
|---------|----------------------|-----------------|
| Platform | Mac only | Mac + iOS |
| Access | External scripts | Within OmniFocus |
| Syntax | Method calls: `task.name()` | Direct properties: `task.name` |
| Application | `Application('OmniFocus')` | `Document.defaultDocument` |
| Collections | Methods: `flattenedTasks()` | Properties: `flattenedTasks` |
| New objects | `new Task()` | `new Task()` |
| Execution | `osascript -l JavaScript` | OmniFocus menu/automation |

**Key Difference:**
```javascript
// JXA (AppleScript bridge)
const name = task.name();
task.name = "New name";
const tasks = doc.flattenedTasks();

// Omni Automation
const name = task.name;
task.name = "New name";
const tasks = doc.flattenedTasks;
```

---

## Getting Started

### Prerequisites

- **macOS** with OmniFocus installed
- **Text editor** for writing scripts
- **Terminal** access
- **Basic JavaScript** knowledge helpful but not required

### Setup and Permissions

#### First Run Permission

When you first run a JXA script, macOS will prompt for automation permissions:

**Grant Automation Permission:**
1. System Preferences → Security & Privacy → Privacy → Automation
2. Find "Terminal" (or your script runner)
3. Enable checkbox for "OmniFocus"

**Alternative:** Grant via command line:
```bash
# Grant Terminal permission to control OmniFocus
sudo sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
  "INSERT or REPLACE INTO access VALUES('kTCCServiceAppleEvents','com.apple.Terminal',0,1,1,NULL,NULL,NULL,'com.omnigroup.OmniFocus3',NULL,0,1234567890);"
```

#### Test Installation

Create a test script `test.js`:

```javascript
#!/usr/bin/osascript -l JavaScript

function run(argv) {
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    const taskCount = doc.flattenedTasks().length;
    console.log(`Found ${taskCount} tasks in OmniFocus`);
}
```

**Run it:**
```bash
chmod +x test.js
./test.js
```

**Expected output:** `Found 42 tasks in OmniFocus` (or your actual count)

### Your First Script

**Create `hello-omnifocus.js`:**

```javascript
#!/usr/bin/osascript -l JavaScript

function run(argv) {
    // Get OmniFocus application
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Get today's tasks
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const tasks = doc.flattenedTasks().filter(task => {
        const due = task.dueDate();
        return due && due >= now && due < tomorrow && !task.completed();
    });

    // Display results
    console.log(`\nYou have ${tasks.length} tasks due today:\n`);
    tasks.forEach((task, index) => {
        console.log(`${index + 1}. ${task.name()}`);
    });
    console.log('');
}
```

**Make executable and run:**
```bash
chmod +x hello-omnifocus.js
./hello-omnifocus.js
```

**What this does:**
1. Accesses OmniFocus via `Application('OmniFocus')`
2. Gets the default document
3. Filters tasks for those due today
4. Displays results

**Next:** See [JXA Quickstart](quickstarts/jxa_quickstart.md) for using libraries to simplify this code.

---

## Using Modular Libraries

### Overview

The omnifocus-manager skill provides modular libraries for common operations. Instead of writing query/mutation logic yourself, import and use these libraries.

**Library location:** `libraries/jxa/`

**Available libraries:**
- `taskQuery.js` - Query operations (today, overdue, flagged, search)
- `taskMutation.js` - Create, update, complete, delete tasks
- `dateUtils.js` - Date parsing and formatting helpers
- `argParser.js` - Command-line argument parsing

**See:** [Libraries README](../libraries/README.md) for complete documentation.

### Loading Libraries

**Pattern: Foundation Framework Loader**

```javascript
#!/usr/bin/osascript -l JavaScript

ObjC.import('Foundation');

// Helper function to load library
function loadLibrary(filename) {
    const path = '../../libraries/jxa/' + filename;
    return eval($.NSString.alloc.initWithContentsOfFileEncodingError(
        path, $.NSUTF8StringEncoding, null
    ).js);
}

function run(argv) {
    // Load libraries
    const taskQuery = loadLibrary('taskQuery.js');
    const dateUtils = loadLibrary('dateUtils.js');

    // Use library functions
    const app = Application('OmniFocus');
    const tasks = taskQuery.getTodayTasks(app.defaultDocument);

    console.log(`Found ${tasks.length} tasks today`);
}
```

**Key points:**
- `ObjC.import('Foundation')` - Required for file I/O
- `loadLibrary()` - Reads and evaluates library code
- Relative or absolute paths work
- Use absolute paths for cron jobs

### Using taskQuery Library

```javascript
const taskQuery = loadLibrary('taskQuery.js');
const app = Application('OmniFocus');
const doc = app.defaultDocument;

// Query operations
const today = taskQuery.getTodayTasks(doc);           // Due/deferred today
const overdue = taskQuery.getOverdueTasks(doc);       // Past due
const dueSoon = taskQuery.getDueSoon(doc, 7);         // Due within 7 days
const flagged = taskQuery.getFlagged(doc);            // Flagged tasks
const search = taskQuery.searchTasks(doc, "meeting"); // Search by name/note

// Format task info
const taskInfo = taskQuery.formatTaskInfo(task);
```

### Using taskMutation Library

```javascript
const taskMutation = loadLibrary('taskMutation.js');
const app = Application('OmniFocus');
const doc = app.defaultDocument;

// Create task
const result = taskMutation.createTask(app, doc, {
    name: "Call dentist",
    project: "Health",
    tags: "phone,urgent",
    due: new Date("2025-12-30"),
    flagged: true,
    createProject: true,
    createTags: true
});

console.log(`Created: ${result.name} (ID: ${result.id})`);

// Update task
taskMutation.updateTask(app, doc, "Task name", {
    flagged: true,
    due: new Date("2025-12-31")
});

// Complete task
taskMutation.completeTask(doc, "Task name");
```

### Using dateUtils Library

```javascript
const dateUtils = loadLibrary('dateUtils.js');

// Parse dates
const date = dateUtils.parseDate("2025-12-30");        // ISO string → Date
const estimate = dateUtils.parseEstimate("1h30m");     // Returns 90 (minutes)

// Format dates
const iso = dateUtils.formatDate(new Date());          // Date → ISO string

// Date checks
const isToday = dateUtils.isToday(task.dueDate());     // Boolean
```

### Using argParser Library

```javascript
const argParser = loadLibrary('argParser.js');

function run(argv) {
    const args = argParser.parseArgs(argv);

    // argv: ["create", "--name", "Task", "--flagged"]
    // args: { action: "create", name: "Task", flagged: true }

    if (args.help) {
        argParser.printHelp();
        return;
    }

    // Use parsed arguments...
}
```

### Complete Example with Libraries

**Create `daily-report.js`:**

```javascript
#!/usr/bin/osascript -l JavaScript

ObjC.import('Foundation');

function loadLibrary(filename) {
    const path = '../../libraries/jxa/' + filename;
    return eval($.NSString.alloc.initWithContentsOfFileEncodingError(
        path, $.NSUTF8StringEncoding, null
    ).js);
}

function run(argv) {
    // Load libraries
    const taskQuery = loadLibrary('taskQuery.js');
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Get data
    const today = taskQuery.getTodayTasks(doc);
    const overdue = taskQuery.getOverdueTasks(doc);
    const flagged = taskQuery.getFlagged(doc);

    // Display report
    console.log('\n=== DAILY REPORT ===\n');
    console.log(`Today: ${today.length} tasks`);
    console.log(`Overdue: ${overdue.length} tasks`);
    console.log(`Flagged: ${flagged.length} tasks\n`);

    if (overdue.length > 0) {
        console.log('⚠️  OVERDUE TASKS:');
        overdue.forEach(t => console.log(`  - ${t.name}`));
        console.log('');
    }
}
```

**See also:**
- [Standalone examples](../assets/examples/standalone/) - Minimal library usage
- [JXA script examples](../assets/examples/jxa-scripts/) - Complete workflows
- [Libraries README](../libraries/README.md) - Complete API documentation

---

## AppleScript API Reference

Complete reference for the OmniFocus AppleScript API accessible through JXA.

### Application Object

The root object for accessing OmniFocus.

```javascript
const omniFocus = Application('OmniFocus');
const doc = omniFocus.defaultDocument;
```

#### Properties

- `version` (text) - OmniFocus version number
- `defaultDocument` (document) - The main OmniFocus document
- `name` (text) - Application name ("OmniFocus")

### Document Object

The main container for all OmniFocus data.

#### Accessing the Document

```javascript
const doc = Application('OmniFocus').defaultDocument;
```

#### Properties

- `name` (text) - Document name
- `modified` (boolean) - Whether document has unsaved changes
- `path` (text) - File path to document

#### Collections

**Projects:**
```javascript
// Get all projects (top-level only)
doc.projects()

// Get all projects including nested
doc.flattenedProjects()
```

**Tasks:**
```javascript
// Get inbox tasks
doc.inboxTasks()

// Get all tasks (flattened hierarchy)
doc.flattenedTasks()
```

**Tags:**
```javascript
// Get all tags
doc.flattenedTags()
```

**Folders:**
```javascript
// Get all folders
doc.folders()

// Get flattened folders
doc.flattenedFolders()
```

#### Methods

- `save()` - Save the document
- `undo()` - Undo last action
- `redo()` - Redo last undone action

### Task Object

Represents an individual task in OmniFocus.

#### Basic Properties

- `name` (text) - Task name
- `note` (text) - Task note/description
- `id` (text) - Persistent identifier (read-only)
- `completed` (boolean) - Completion status (read-only)
- `completionDate` (date) - When task was completed
- `dropped` (boolean) - Whether task is dropped (read-only)
- `dropDate` (date) - When task was dropped

#### Scheduling Properties

- `dueDate` (date) - When task is due
- `deferDate` (date) - When task should start (defer until)
- `effectiveDueDate` (date) - Inherited or explicit due date (read-only)
- `effectiveDeferDate` (date) - Inherited or explicit defer date (read-only)

#### Status Properties

- `flagged` (boolean) - Whether task is flagged
- `taskStatus` (enum) - Current status (read-only)
  - `Available` - Can be worked on now
  - `Blocked` - Waiting on other tasks
  - `Completed` - Finished
  - `Dropped` - Abandoned
  - `DueSoon` - Due within 24 hours
  - `Next` - Next available task in sequential project
  - `Overdue` - Past due date

#### Organization Properties

- `containingProject` (project) - Parent project (read-only)
- `parentTask` (task) - Parent task if this is a subtask (read-only)
- `tasks` (list of tasks) - Child tasks
- `sequential` (boolean) - Whether children must be done in order
- `repetitionRule` (text) - Recurrence pattern
- `numberOfAvailableTasks` (integer) - Available child tasks (read-only)
- `numberOfCompletedTasks` (integer) - Completed child tasks (read-only)

#### Time Properties

- `estimatedMinutes` (integer) - Time estimate in minutes
- `repetition` (repetition) - Recurrence settings

#### Tag Properties

- `tags` (list of tags) - Tags assigned to task
- `primaryTag` (tag) - First tag in list (read-only)

#### Attachment Properties

- `attachments` (list of attachments) - File attachments
- `linkedFileURLs` (list of text) - URLs to linked files

#### Task Methods

**Completion:**
```javascript
// Mark complete
task.markComplete();

// Mark complete with specific date
task.markComplete(new Date());

// Mark incomplete
task.markIncomplete();
```

**Dropping:**
```javascript
// Drop the task
task.drop();

// Drop with specific date
task.drop(allOccurrences = false);
```

**Tags:**
```javascript
// Add single tag
task.addTag(tagObject);

// Add multiple tags
task.addTags([tag1, tag2, tag3]);

// Remove tag
task.removeTag(tagObject);

// Remove multiple tags
task.removeTags([tag1, tag2]);

// Clear all tags
task.clearTags();
```

**Attachments:**
```javascript
// Add attachment
task.addAttachment(fileWrapper);

// Add linked file URL
task.addLinkedFileURL("file:///path/to/file");

// Remove attachment by index
task.removeAttachmentAtIndex(0);
```

### Project Object

Represents a project containing tasks.

#### Basic Properties

- `name` (text) - Project name
- `note` (text) - Project description
- `id` (text) - Persistent identifier (read-only)
- `status` (enum) - Project status
  - `active` - Currently working on
  - `on hold` - Paused
  - `completed` - Finished
  - `dropped` - Abandoned

#### Scheduling Properties

- `dueDate` (date) - When project is due
- `deferDate` (date) - When project should start
- `completionDate` (date) - When project was completed

#### Status Properties

- `flagged` (boolean) - Whether project is flagged
- `completedByChildren` (boolean) - Auto-complete when all children complete
- `sequential` (boolean) - Whether tasks must be done in order
- `singleton action list` (boolean) - Whether this is a single action list

#### Organization Properties

- `parentFolder` (folder) - Containing folder (read-only)
- `containingProject` (project) - Parent project if this is a subproject (read-only)
- `tasks` (list of tasks) - Tasks in this project
- `flattenedTasks` (list of tasks) - All tasks including in subprojects (read-only)
- `rootTask` (task) - The project as a task object (read-only)

#### Statistics Properties

- `numberOfAvailableTasks` (integer) - Available tasks (read-only)
- `numberOfCompletedTasks` (integer) - Completed tasks (read-only)
- `numberOfDueTasks` (integer) - Tasks due soon (read-only)

#### Tag Properties

- `tags` (list of tags) - Tags assigned to project

#### Project Methods

```javascript
// Mark complete
project.markComplete();

// Mark incomplete
project.markIncomplete();
```

### Tag Object

Represents a tag (formerly called "context").

#### Properties

- `name` (text) - Tag name
- `id` (text) - Persistent identifier (read-only)
- `active` (boolean) - Whether tag is active
- `hidden` (boolean) - Whether tag is hidden
- `availableTaskCount` (integer) - Number of available tasks with this tag (read-only)
- `remainingTaskCount` (integer) - Number of remaining tasks with this tag (read-only)
- `parent` (tag) - Parent tag if nested (read-only)

### Folder Object

Represents a folder containing projects.

#### Properties

- `name` (text) - Folder name
- `id` (text) - Persistent identifier (read-only)
- `status` (enum) - Folder status
  - `active`
  - `on hold`
  - `dropped`

#### Organization Properties

- `parentFolder` (folder) - Parent folder if nested (read-only)
- `projects` (list of projects) - Projects in this folder
- `folders` (list of folders) - Subfolders
- `flattenedProjects` (list of projects) - All projects including in subfolders (read-only)
- `flattenedFolders` (list of folders) - All subfolders recursively (read-only)

### Creating Objects

#### Creating Tasks

```javascript
// Create new task
const task = new Task("Task name");

// Set properties
task.note = "Task description";
task.dueDate = new Date("2025-12-25");
task.flagged = true;

// Add to inbox
doc.inboxTasks.push(task);

// Or add to project
project.tasks.push(task);
```

#### Creating Projects

```javascript
// Create new project
const project = new Project("Project name");

// Set properties
project.note = "Project description";
project.sequential = true;
project.deferDate = new Date("2025-12-20");

// Add to document
doc.projects.push(project);

// Or add to folder
folder.projects.push(project);
```

#### Creating Tags

```javascript
// Create new tag
const tag = new Tag("Tag name");

// Set properties
tag.active = true;

// Add to document
doc.flattenedTags.push(tag);
```

#### Creating Folders

```javascript
// Create new folder
const folder = new Folder("Folder name");

// Add to document
doc.folders.push(folder);

// Or add to another folder
parentFolder.folders.push(folder);
```

### Querying and Filtering

#### Finding Objects

```javascript
// Find project by name
const project = doc.flattenedProjects().find(p => p.name() === "Project Name");

// Find task by ID
const task = doc.flattenedTasks().find(t => t.id() === "abc123xyz");

// Find tag by name
const tag = doc.flattenedTags().find(t => t.name() === "urgent");
```

#### Filtering Tasks

**Active tasks:**
```javascript
const activeTasks = doc.flattenedTasks().filter(t =>
    !t.completed() && !t.dropped()
);
```

**Flagged tasks:**
```javascript
const flaggedTasks = doc.flattenedTasks().filter(t =>
    t.flagged() && !t.completed()
);
```

**Tasks due today:**
```javascript
const today = new Date();
today.setHours(0, 0, 0, 0);
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);

const dueToday = doc.flattenedTasks().filter(t => {
    const due = t.dueDate();
    return due && due >= today && due < tomorrow && !t.completed();
});
```

**Tasks with specific tag:**
```javascript
const tag = doc.flattenedTags().find(t => t.name() === "work");
const workTasks = doc.flattenedTasks().filter(t =>
    t.tags().some(taskTag => taskTag.id() === tag.id())
);
```

**Tasks in project:**
```javascript
const projectTasks = project.flattenedTasks().filter(t => !t.completed());
```

**Recommendation:** Use the `taskQuery` library for common filters instead of writing these yourself.

### Date Handling

#### Creating Dates

```javascript
// From string (ISO 8601)
const date = new Date("2025-12-25T14:30:00");

// From components
const date = new Date(2025, 11, 25, 14, 30, 0);  // Month is 0-indexed!

// Current date
const now = new Date();

// Relative dates
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);

const nextWeek = new Date();
nextWeek.setDate(nextWeek.getDate() + 7);
```

#### Comparing Dates

```javascript
const due = task.dueDate();
const now = new Date();

if (due < now) {
    // Overdue
} else if (due > now) {
    // Future
}
```

#### Clearing Dates

```javascript
// Set to null to clear
task.dueDate = null;
task.deferDate = null;
```

**Recommendation:** Use the `dateUtils` library for parsing and formatting dates.

### Error Handling

```javascript
try {
    const task = doc.flattenedTasks().find(t => t.name() === "Task Name");
    if (!task) {
        throw new Error("Task not found");
    }
    task.markComplete();
} catch (error) {
    console.error("Error:", error.message);
}
```

### Common Patterns

#### Creating Task with Full Details

```javascript
const task = new Task("Complete project proposal");
task.note = "Include budget, timeline, and deliverables";
task.dueDate = new Date("2025-12-31");
task.deferDate = new Date("2025-12-20");
task.estimatedMinutes = 120;
task.flagged = true;

// Find or create project
let project = doc.flattenedProjects().find(p => p.name() === "Q4 Projects");
if (!project) {
    project = new Project("Q4 Projects");
    doc.projects.push(project);
}

// Add task to project
project.tasks.push(task);

// Add tags
const urgentTag = doc.flattenedTags().find(t => t.name() === "urgent");
if (urgentTag) {
    task.addTag(urgentTag);
}
```

**Better approach:** Use the `taskMutation` library which handles all this for you.

#### Batch Completion

```javascript
// Complete all tasks in a project
const project = doc.flattenedProjects().find(p => p.name() === "Old Project");
if (project) {
    project.flattenedTasks().forEach(task => {
        if (!task.completed()) {
            task.markComplete();
        }
    });
}
```

#### Rescheduling Tasks

```javascript
// Move all overdue tasks to next week
const now = new Date();
const nextWeek = new Date();
nextWeek.setDate(nextWeek.getDate() + 7);

doc.flattenedTasks().forEach(task => {
    const due = task.dueDate();
    if (due && due < now && !task.completed()) {
        task.dueDate = nextWeek;
    }
});
```

---

## CLI Command Reference

Reference for the `manage_omnifocus.js` script - complete command-line interface for OmniFocus.

**Script location:** `scripts/manage_omnifocus.js`

**Execution:** `osascript -l JavaScript scripts/manage_omnifocus.js <command> [options]`

**Output format:** JSON for all operations

**Note:** This script will be replaced by `scripts/omnifocus.js` with improved JSON I/O in Phase 5 of the refactoring. The API will remain similar but with enhanced structure.

### Query Commands

#### Today's Tasks

Shows tasks due today or deferred until today.

```bash
osascript -l JavaScript scripts/manage_omnifocus.js today
```

**Use when:** User asks "what's on my agenda?" or "what should I do today?"

**Output:** JSON with task details (name, project, due date, tags, etc.)

#### List Active Tasks

Returns all incomplete tasks that are available to work on (not blocked or deferred to future).

```bash
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active
```

**Filters:** `active`, `completed`, `dropped`, `all`

**Examples:**
```bash
# Active tasks only (default)
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active

# All tasks including completed
osascript -l JavaScript scripts/manage_omnifocus.js list --filter all

# Completed tasks only
osascript -l JavaScript scripts/manage_omnifocus.js list --filter completed

# Dropped tasks only
osascript -l JavaScript scripts/manage_omnifocus.js list --filter dropped
```

#### Tasks Due Soon

Shows tasks due within the next N days (default: 7).

```bash
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
```

**Use when:** User asks "what's due this week?" or "what's coming up?"

**Examples:**
```bash
# Next 7 days (default)
osascript -l JavaScript scripts/manage_omnifocus.js due-soon

# Next 3 days
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 3

# Next 30 days
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 30
```

#### Flagged Tasks

Lists all flagged tasks.

```bash
osascript -l JavaScript scripts/manage_omnifocus.js flagged
```

**Use when:** User asks about priorities or important items.

#### Search for Tasks

Searches task names and notes for the specified term.

```bash
osascript -l JavaScript scripts/manage_omnifocus.js search --query "meeting"
```

**Use when:** User asks "find tasks about X" or "what meetings do I have?"

**Examples:**
```bash
# Search for "meeting"
osascript -l JavaScript scripts/manage_omnifocus.js search --query "meeting"

# Search for "project review"
osascript -l JavaScript scripts/manage_omnifocus.js search --query "project review"
```

#### Output Format

All query commands return JSON output:

```json
{
  "success": true,
  "count": 3,
  "tasks": [
    {
      "id": "abc123",
      "name": "Task name",
      "project": "Project name",
      "dueDate": "2025-12-20T17:00:00.000Z",
      "flagged": false,
      "tags": ["tag1", "tag2"],
      "note": "Task notes"
    }
  ]
}
```

**Processing output with jq:**
```bash
# Get just task names
osascript -l JavaScript scripts/manage_omnifocus.js today | jq '.tasks[] | .name'

# Get tasks with due dates
osascript -l JavaScript scripts/manage_omnifocus.js due-soon | jq '.tasks[] | {name, dueDate}'

# Count flagged tasks
osascript -l JavaScript scripts/manage_omnifocus.js flagged | jq '.count'
```

### Task Management Commands

#### Creating Tasks

**Simple inbox task:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create --name "Call dentist"
```

**Task with project:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Review proposal" \
  --project "Work"
```

**Create project if it doesn't exist:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "New task" \
  --project "New Project" \
  --create-project
```

**Task with due date:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Submit report" \
  --due "2025-12-25"
```

**Date format:** ISO 8601: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`

**Examples:**
```bash
# Date only
--due "2025-12-25"

# Date and time
--due "2025-12-25T14:00:00"

# With timezone
--due "2025-12-25T14:00:00-08:00"
```

**Task with tags:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Call client" \
  --tags "phone,urgent"
```

**Create tags if they don't exist:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Call client" \
  --tags "phone,urgent" \
  --create-tags
```

**Flagged task:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Important task" \
  --flagged
```

**Task with note:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Research topic" \
  --note "Key points to investigate: API design, performance, security"
```

**Task with time estimate:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Write documentation" \
  --estimate "2h30m"
```

**Format:** `30m`, `2h`, or `1h30m`

**Examples:**
```bash
--estimate "30m"      # 30 minutes
--estimate "2h"       # 2 hours
--estimate "1h30m"    # 1 hour 30 minutes
--estimate "90m"      # 90 minutes (same as 1h30m)
```

**Complete task creation example:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Project kickoff meeting" \
  --project "Q4 Planning" \
  --tags "meeting,important" \
  --due "2025-12-30T14:00:00" \
  --defer "2025-12-28" \
  --estimate "1h30m" \
  --note "Prepare slides and metrics" \
  --flagged \
  --create-project \
  --create-tags
```

#### Updating Tasks

Update tasks by name or ID. If multiple tasks share the same name, use `--id` instead of `--name`.

**Update task name:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Old name" \
  --new-name "New name"
```

**Update due date:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --due "2025-12-31"
```

**Clear due date:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --due clear
```

**Update project:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --project "Different Project"
```

**Move to inbox:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --project inbox
```

**Update tags:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --tags "new,tags,here"
```

**Clear all tags:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --tags ""
```

**Update multiple properties:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --new-name "Updated name" \
  --due "2025-12-31" \
  --flagged \
  --note "Updated note text"
```

#### Completing Tasks

```bash
osascript -l JavaScript scripts/manage_omnifocus.js complete --name "Task to complete"
```

**Use ID for duplicate names:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js complete --id "abc123xyz"
```

#### Deleting Tasks

```bash
osascript -l JavaScript scripts/manage_omnifocus.js delete --name "Task to delete"
```

**Warning:** Deletion is permanent. Consider completing tasks instead when possible.

#### Getting Task Information

Retrieve detailed information about a task:

```bash
osascript -l JavaScript scripts/manage_omnifocus.js info --name "Task name"
```

**Returns JSON with:**
- Task ID
- Name, note
- Completion status
- Due and defer dates
- Flag status
- Time estimate
- Project
- Tags

**Use when:**
- Checking task details before updating
- Getting task ID for operations requiring unique identification
- Verifying task existence

#### Handling Duplicate Task Names

If multiple tasks share the same name, the script will return an error listing all matching tasks with their IDs and projects:

```bash
osascript -l JavaScript scripts/manage_omnifocus.js info --name "Meeting"
```

**Output:**
```json
{
  "success": false,
  "error": "Multiple tasks found",
  "tasks": [
    { "id": "abc123", "name": "Meeting", "project": "Work" },
    { "id": "def456", "name": "Meeting", "project": "Personal" }
  ]
}
```

**Then use the specific ID:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update --id "abc123" --due "2025-12-31"
```

### Getting Help

All commands include built-in help:

```bash
osascript -l JavaScript scripts/manage_omnifocus.js help
```

---

## Best Practices

### Use IDs for Reliability

```javascript
// Store task ID
const taskId = task.id();

// Later, find by ID (reliable even if name changes)
const task = doc.flattenedTasks().find(t => t.id() === taskId);
```

### Check Existence Before Operations

```javascript
const task = doc.flattenedTasks().find(t => t.name() === "Task Name");
if (task) {
    // Safe to operate on task
    task.markComplete();
} else {
    console.error("Task not found");
}
```

### Use Flattened Collections

```javascript
// Prefer this (gets all tasks including nested)
doc.flattenedTasks()

// Over this (only gets top-level tasks)
doc.inboxTasks()
```

### Handle Multiple Matches

```javascript
const matches = doc.flattenedTasks().filter(t => t.name() === "Meeting");

if (matches.length === 0) {
    console.error("No tasks found");
} else if (matches.length === 1) {
    // Single match, safe to proceed
    matches[0].markComplete();
} else {
    // Multiple matches, need user to clarify
    console.error("Multiple tasks found:", matches.map(t => ({
        id: t.id(),
        name: t.name(),
        project: t.containingProject() ? t.containingProject().name() : "Inbox"
    })));
}
```

### Use Modular Libraries

```javascript
// Instead of writing complex queries yourself
const today = new Date();
today.setHours(0, 0, 0, 0);
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);
const dueToday = doc.flattenedTasks().filter(t => {
    const due = t.dueDate();
    return due && due >= today && due < tomorrow && !t.completed();
});

// Use the taskQuery library
const taskQuery = loadLibrary('taskQuery.js');
const dueToday = taskQuery.getTodayTasks(doc);
```

**Benefits:**
- Less code to write and maintain
- Tested and reliable
- Consistent across scripts
- Easier to read and understand

### Date Format Standards

Always use ISO 8601 format:
- Date only: `2025-12-25`
- Date and time: `2025-12-25T14:30:00`
- With timezone: `2025-12-25T14:30:00-08:00`

**Use dateUtils library for parsing:**
```javascript
const dateUtils = loadLibrary('dateUtils.js');
const date = dateUtils.parseDate("2025-12-25");
```

### Script Organization

**Good structure:**
```javascript
#!/usr/bin/osascript -l JavaScript

ObjC.import('Foundation');

// Load libraries at top
function loadLibrary(filename) { /* ... */ }

// Helper functions
function formatTask(task) { /* ... */ }
function displayResults(tasks) { /* ... */ }

// Main function
function run(argv) {
    const taskQuery = loadLibrary('taskQuery.js');
    const app = Application('OmniFocus');

    const tasks = taskQuery.getTodayTasks(app.defaultDocument);
    displayResults(tasks);
}
```

---

## Troubleshooting

### "Application isn't running" error

**Problem:** OmniFocus must be running to use the AppleScript API.

**Solutions:**
```javascript
// Option 1: Launch OmniFocus first
const app = Application('OmniFocus');
app.activate();

// Option 2: Check if running
const systemEvents = Application('System Events');
const isRunning = systemEvents.processes.whose({ name: 'OmniFocus' }).length > 0;
if (!isRunning) {
    const app = Application('OmniFocus');
    app.activate();
}
```

### Library not found

**Problem:** Script can't find library file.

**Solutions:**
```javascript
// Use absolute paths for cron jobs
const path = '/full/path/to/libraries/jxa/taskQuery.js';

// Use relative paths for manual execution
const path = '../../libraries/jxa/taskQuery.js';

// Debug: Print current directory
console.log($.NSFileManager.defaultManager.currentDirectoryPath.js);
```

### Permission denied

**Problem:** macOS hasn't granted automation permissions.

**Solutions:**
1. Make script executable: `chmod +x script.js`
2. Grant Terminal accessibility permissions:
   - System Preferences → Security & Privacy → Privacy → Automation
   - Enable Terminal → OmniFocus

### Dates showing wrong timezone

**Problem:** JXA dates are in local timezone by default.

**Solutions:**
```javascript
// Use .toISOString() for UTC
const utc = task.dueDate().toISOString();

// Or use dateUtils library
const dateUtils = loadLibrary('dateUtils.js');
const formatted = dateUtils.formatDate(task.dueDate());
```

### "Task not found" errors

**Problem:** Task name doesn't match or task is nested.

**Solutions:**
```javascript
// Use flattenedTasks() not inboxTasks()
const task = doc.flattenedTasks().find(t => t.name() === "Task Name");

// Check for partial matches
const matches = doc.flattenedTasks().filter(t =>
    t.name().toLowerCase().includes("task name".toLowerCase())
);

// Use task ID for reliability
const task = doc.flattenedTasks().find(t => t.id() === taskId);
```

### Script runs slow with large databases

**Problem:** Filtering all tasks is slow.

**Solutions:**
```javascript
// Use early termination
const task = doc.flattenedTasks().find(t => t.id() === targetId);
// Stops at first match instead of checking all tasks

// Cache results
const allTasks = doc.flattenedTasks();  // Call once
const today = allTasks.filter(/* ... */);
const overdue = allTasks.filter(/* ... */);

// Use specific collections
const inboxOnly = doc.inboxTasks();  // Faster than flattenedTasks()
```

### Error handling best practices

```javascript
try {
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Your code here

} catch (error) {
    console.error("Error:", error.message);
    console.error("Stack:", error.stack);

    // Return structured error for parsing
    console.log(JSON.stringify({
        success: false,
        error: error.message
    }));
}
```

---

## Resources

### Documentation

**Local documentation:**
- **JXA Quickstart:** [quickstarts/jxa_quickstart.md](quickstarts/jxa_quickstart.md) - 5-minute tutorial
- **Libraries README:** [../libraries/README.md](../libraries/README.md) - Complete library API
- **Examples:** [../assets/examples/](../assets/examples/) - Standalone scripts and complete workflows
- **OmniFocus API:** [OmniFocus-API.md](OmniFocus-API.md) - Comprehensive API reference

**External resources:**
- **OmniFocus AppleScript Documentation:** [support.omnigroup.com/omnifocus-applescript](https://support.omnigroup.com/omnifocus-applescript/)
- **Mac Automation Scripting Guide:** [developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- **JXA Cookbook:** [github.com/JXA-Cookbook/JXA-Cookbook](https://github.com/JXA-Cookbook/JXA-Cookbook)

### Scripting Dictionary

To view the complete OmniFocus scripting dictionary on your Mac:

```bash
# Extract dictionary to XML
sdef /Applications/OmniFocus.app > omnifocus_dictionary.xml

# View in Script Editor
open -a "Script Editor" /Applications/OmniFocus.app
# Then: File → Open Dictionary → OmniFocus
```

### Example Usage

**Standalone examples:** [../assets/examples/standalone/](../assets/examples/standalone/)
- `query-today.js` - Load and use taskQuery library
- `create-task.js` - Load and use taskMutation library
- `build-url.js` - Load and use urlBuilder library

**Complete JXA scripts:** [../assets/examples/jxa-scripts/](../assets/examples/jxa-scripts/)
- `check-today.js` - Daily task report with priority ranking
- `bulk-create.js` - Create multiple tasks from templates
- `weekly-review.js` - Complete GTD weekly review
- `generate-report.js` - Export tasks to various formats

### Getting Help

For issues with:
- **JXA syntax:** See Mac Automation Scripting Guide
- **OmniFocus API:** See OmniFocus AppleScript documentation or scripting dictionary
- **Libraries:** See [../libraries/README.md](../libraries/README.md)
- **Script issues:** Check Troubleshooting section above

---

## What's Next?

**Beginner:**
- Work through the [JXA Quickstart](quickstarts/jxa_quickstart.md)
- Run the standalone examples
- Modify examples for your workflows

**Intermediate:**
- Create automation scripts using libraries
- Set up cron jobs or Alfred workflows
- Combine multiple libraries

**Advanced:**
- Create custom library functions
- Direct SQLite database queries (see [database_schema.md](database_schema.md))
- Integrate with other automation tools

**Want cross-platform?** See the [Plugin Development Guide](plugin_development_guide.md) to create OmniFocus plugins that work on Mac + iOS.
