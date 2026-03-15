# JXA Guide for OmniFocus

This is the complete guide to automating OmniFocus from the command line on macOS using JavaScript for Automation (JXA).

## 1. What is JXA?

**JavaScript for Automation (JXA)** is Apple's technology that allows you to control macOS applications using JavaScript. It acts as a bridge to the application's underlying AppleScript automation interface.

**Key Characteristics:**
*   **macOS only**: JXA is part of macOS and is not available on iOS or iPadOS.
*   **External Scripts**: You write `.js` files and execute them from the command line using `osascript`.
*   **Full API Access**: It provides complete access to OmniFocus's traditional AppleScript API.
*   **Method Call Syntax**: Because it's a bridge to AppleScript, properties are accessed via method calls, e.g., `task.name()`, not `task.name`.

### When to Use JXA vs. Omni Automation

*   **Use JXA (this guide)** for command-line automation, integrating OmniFocus with other Mac apps, and scheduled tasks (cron, launchd).
*   **Use Omni Automation** for creating cross-platform (Mac & iOS) plugins that integrate directly into the OmniFocus user interface. See `omni_automation_guide.md` for details.

**Key Syntactic Difference:**
```javascript
// JXA (AppleScript bridge)
const name = task.name(); // Properties are functions
task.name = "New name";
const tasks = doc.flattenedTasks(); // Collections are functions

// Omni Automation (Native JavaScript)
const name = task.name; // Properties are direct
task.name = "New name";
const tasks = doc.flattenedTasks; // Collections are properties
```

## 2. Quick Start: Your First JXA Script

This 5-minute tutorial will create a script to show today's tasks.

### Step 1: Your First Script

Create a file named `today.js`:

```javascript
#!/usr/bin/osascript -l JavaScript

function run(argv) {
    // Get a reference to the OmniFocus application
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Get all tasks
    const allTasks = doc.flattenedTasks();

    // Filter for today's tasks
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const todayTasks = allTasks.filter(task => {
        if (task.completed() || task.dropped()) return false;
        const due = task.dueDate();
        const defer = task.deferDate();
        return (due && due >= now && due < tomorrow) ||
               (defer && defer >= now && defer < tomorrow);
    });

    // Display the results
    console.log(`\nYou have ${todayTasks.length} tasks today:\n`);
    todayTasks.forEach((task, index) => {
        console.log(`${index + 1}. ${task.name()}`);
    });
    console.log('');
}
```

Make the script executable and run it from your terminal:
```bash
chmod +x today.js
./today.js
```
The first time you run it, macOS will ask for permission to allow your terminal to control OmniFocus. You must grant this.

### Step 2: Simplify with Libraries

This skill includes pre-built libraries to simplify common operations. Let's rewrite the script to use the `taskQuery` library.

Create `today-with-library.js`:
```javascript
#!/usr/bin/osascript -l JavaScript

ObjC.import('Foundation');

// Helper function to load a library file
function loadLibrary(path) {
    return eval($.NSString.alloc.initWithContentsOfFileEncodingError(
        path,
        $.NSUTF8StringEncoding,
        null
    ).js);
}

function run(argv) {
    // Load the library
    const taskQuery = loadLibrary('scripts/libraries/jxa/taskQuery.js');

    // Get the OmniFocus document
    const app = Application('OmniFocus');
    const doc = app.defaultDocument;

    // Get today's tasks with one line!
    const tasks = taskQuery.getTodayTasks(doc);

    // Display the results
    console.log(`\nYou have ${tasks.length} tasks today:\n`);
    tasks.forEach((task, index) => {
        console.log(`${index + 1}. ${task.name}`);
    });
    console.log('');
}
```
This version is much cleaner because the library abstracts away the complex date and filtering logic.

## 3. Using the JXA Modular Libraries

This skill's JXA libraries are located in `scripts/libraries/jxa/`.

*   **`taskQuery.js`**: Functions for reading/querying tasks (`getTodayTasks`, `getOverdueTasks`, `searchTasks`, etc.).
*   **`taskMutation.js`**: Functions for writing/changing tasks (`createTask`, `updateTask`, `completeTask`).
*   **`dateUtils.js`**: Helpers for parsing and formatting dates.
*   **`argParser.js`**: For parsing command-line arguments passed to your script.

To use them, include the `loadLibrary` helper function in your script and call it with the path to the library file.

## 4. JXA API Reference

This is a summary of the most common objects and properties available through the JXA bridge.

### Application and Document
*   `Application('OmniFocus')`: The root object.
*   `.defaultDocument`: The main database.
*   `.flattenedTasks()`: Returns a flat array of all task objects.
*   `.flattenedProjects()`: Returns a flat array of all project objects.
*   `.flattenedTags()`: Returns a flat array of all tag objects.

### Task Object
*   `.name()`: The name of the task.
*   `.note()`: The note of the task.
*   `.id()`: The unique ID.
*   `.completed()`: Boolean, is the task complete?
*   `.dueDate()`: The due date.
*   `.deferDate()`: The defer date.
*   `.flagged()`: Boolean, is the task flagged?
*   `.containingProject()`: The parent project object.
*   `.tags()`: An array of tag objects.
*   `.markComplete()`: Method to complete the task.
*   `.addTag(tagObject)`: Method to add a tag.

### Project Object
*   `.name()`: The name of the project.
*   `.status()`: The status (`active`, `on hold`, `completed`, `dropped`).
*   `.tasks()`: An array of the project's top-level tasks.
*   `.flattenedTasks()`: An array of *all* tasks within the project.

### Tag Object
*   `.name()`: The name of the tag.
*   `.tasks()`: An array of tasks associated with the tag.

## Looking Up Tags

Tag names in OmniFocus often contain Unicode characters or emoji (e.g. `"Capture 📥"`, `"Claude Code 🦀"`). Exact string matching with `===` will fail silently or return `undefined`.

**Always use substring matching:**

```javascript
// WRONG — fails when tag name contains Unicode/emoji
const tag = of.flattenedTags().find(t => t.name() === 'Capture');

// CORRECT — case-insensitive substring match
const tag = of.flattenedTags().find(t => t.name().toLowerCase().includes('capture'));
```

## Adding Tags to a Task

The `.addTag()` method on the Task object is not supported in JXA. Use `app.add()` with the `to:` parameter instead:

```javascript
// WRONG — throws type error
task.addTag(tagObject);

// CORRECT
of.add(tagObject, { to: task.tags });
```

## Removing Tags from a Task

`clearTags()` is not supported. Iterate and remove:

```javascript
const tagsToRemove = task.tags().filter(t => t.name().toLowerCase().includes('sometag'));
tagsToRemove.forEach(t => of.remove(t, { from: task.tags }));
```

## 5. Command-Line Interface (`manage_omnifocus.js`)

This skill includes a ready-to-use CLI script for common operations.

**Execution**: `osascript -l JavaScript scripts/manage_omnifocus.js <command> [options]`

### Query Commands
*   `today`: Show tasks due or deferred to today.
*   `due-soon --days 7`: Show tasks due in the next N days.
*   `flagged`: Show all flagged tasks.
*   `search --query "meeting"`: Search tasks by a keyword.

### Management Commands
*   `create --name "My new task"`: Create a new task.
    *   Accepts flags like `--project`, `--tags`, `--due`, `--note`, `--flagged`.
*   `update --name "Old name" --new-name "New name"`: Update a task's properties.
*   `complete --name "Task to complete"`: Mark a task as complete.
*   `info --name "Task name"`: Get detailed JSON for a specific task.

**Example:**
```bash
# Create a new, flagged task in the "Work" project due tomorrow
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Prepare presentation" \
  --project "Work" \
  --due "$(date -v+1d +%Y-%m-%d)" \
  --flagged
```

## 6. Best Practices & Troubleshooting

*   **Permissions**: The first time you run a JXA script, you must grant permissions in `System Settings > Privacy & Security > Automation`.
*   **OmniFocus Must Be Running**: JXA requires the OmniFocus app to be open.
*   **Use IDs for Reliability**: When updating or deleting, task names can be duplicated. Use the unique ID of a task for reliability.
*   **Use Libraries**: Don't reinvent the wheel. The provided libraries handle common cases and error checking.
*   **Date Formats**: Always use ISO 8601 format (`YYYY-MM-DD`) for dates.
*   **Error Handling**: Wrap your code in `try...catch` blocks to handle potential errors gracefully.

For more detailed troubleshooting, see `troubleshooting.md`.

## 7. Script Conventions

### Canonical `loadLibrary` Pattern

All JXA entry-point scripts use the CWD-relative pattern below. Library paths are resolved
against the **skill root** (`skills/omnifocus-manager/`). Both `gtd-queries.js` and
`manage_omnifocus.js` use this identical implementation — copy it verbatim into new scripts.

```javascript
ObjC.import('stdlib');
ObjC.import('Foundation');

/**
 * Load a JXA library by path relative to the skill root (current working directory).
 * Run from the skills/omnifocus-manager/ root so paths resolve correctly.
 * Libraries use IIFE pattern and return their namespace object via eval().
 */
function loadLibrary(relativePath) {
    const cwd = $.NSFileManager.defaultManager.currentDirectoryPath.js;
    const libPath = cwd + '/' + relativePath;
    const content = $.NSString.alloc.initWithContentsOfFileEncodingError(
        libPath, $.NSUTF8StringEncoding, null
    );
    if (!content) throw new Error('Cannot load library: ' + libPath);
    return eval(content.js);
}

// Path is relative to skill root — scripts/ prefix required
const taskQuery = loadLibrary('scripts/libraries/jxa/taskQuery.js');
```

**Key points:**
- CWD must be `skills/omnifocus-manager/` when the script runs — callers are responsible for this
- `scripts/libraries/jxa/<filename>` is the correct path from the skill root
- `eval(content.js)` is required — `.js` converts NSString to a JS string before eval
- Never destructure methods off a loaded library — call as `taskQuery.getInboxTasks(doc)`,
  not `const {getInboxTasks} = taskQuery` (breaks `this` binding inside the library)

### ❌ Anti-pattern: wrong working directory in the shell caller

```bash
# DO NOT do this in shell wrappers
cd "$SCRIPTS_DIR"                    # CWD = .../skills/omnifocus-manager/scripts/
osascript -l JavaScript gtd-queries.js --action inbox-count
# loadLibrary constructs: .../scripts/scripts/libraries/jxa/taskQuery.js  ← doesn't exist
```

This was the root cause of the weekly-review query failure (issue #71).

### Shell Wrapper Conventions

- Shell scripts that invoke JXA scripts must `cd` to the **skill root**
  (`skills/omnifocus-manager/`), not into `scripts/`
- Reference JXA scripts with the `scripts/` prefix: `osascript -l JavaScript scripts/gtd-queries.js`
- Commands (`.md` files) reference scripts via `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/`
- Run `bash scripts/test-queries.sh` from the skill root to validate before a version bump
