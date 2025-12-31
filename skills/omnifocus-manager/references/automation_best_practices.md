# OmniFocus Automation Best Practices

This reference consolidates proven patterns and best practices for OmniFocus Omni Automation scripting based on official documentation and the OmniFocus scripting model.

**📍 Related Documentation:**
- **[Plugin Development Guide](plugin_development_guide.md)** - Complete plugin creation guide
- **[JXA API Guide](jxa_api_guide.md)** - Command-line automation reference
- **[Libraries README](../libraries/README.md)** - Modular library system for reusable patterns
- **[Workflows Guide](workflows.md)** - Ready-to-use automation patterns

**💡 Key Recommendation:** Use the modular library system (`libraries/`) instead of writing automation from scratch. Libraries provide tested, reusable patterns for common operations.

## Core Principles

### 1. Database-Centric Architecture

**Pattern:** Access the database directly rather than traversing through document objects.

The OmniFocus scripting model centers around the database as the primary data repository. Scripts should target the database directly for efficiency and clarity.

**Recommended approach:**
```javascript
const doc = Application('OmniFocus').defaultDocument;
const database = doc.flattenedTasks; // Direct access to all tasks
```

**Key database properties:**
- `library` - Top-level Projects and Folders
- `inbox` - Tasks in the Inbox perspective
- `tags` - Top-level Tags
- `projects` - All top-level projects
- `folders` - All top-level folders

### 2. Hierarchical Traversal: apply() vs forEach()

**Critical distinction:** OmniFocus has a hierarchical structure. Choose the right iteration method.

**forEach() - Top-level only:**
```javascript
// Only processes top-level items, not nested children
database.projects.forEach(project => {
    console.log(project.name());
});
```

**apply() - Recursive traversal:**
```javascript
// Recursively processes entire hierarchy including nested items
database.projects.apply(project => {
    console.log(project.name()); // Includes sub-projects
});
```

**When to use:**
- **forEach()** - When operating on a single level (e.g., top-level projects only)
- **apply()** - When processing nested structures (e.g., all tasks including subtasks)

### 3. Flattened Collections for Efficient Searching

**Pattern:** Use flattened properties to search across entire hierarchies without manual recursion.

**Available flattened collections:**
- `flattenedTasks` - All tasks at all levels
- `flattenedProjects` - All projects including sub-projects
- `flattenedFolders` - All folders including sub-folders
- `flattenedTags` - All tags including sub-tags

**Example - Search all tasks:**
```javascript
const doc = Application('OmniFocus').defaultDocument;
const allTasks = doc.flattenedTasks();
const meetingTasks = allTasks.filter(task => task.name().includes("meeting"));
```

**Benefits:**
- No need to write recursive traversal code
- Returns hierarchies flattened into arrays
- Enables efficient filtering and searching

### 4. Selection-Based Operations

**Pattern:** Operate on user-selected items through the selection API.

Access selected objects to make scripts responsive to user context:

```javascript
const doc = Application('OmniFocus').defaultDocument;
const win = doc.windows[0];
const selectedTasks = win.selection.tasks;
const selectedProjects = win.selection.projects;
const selectedFolders = win.selection.folders;
```

**Use cases:**
- Scripts that act on whatever the user has selected
- Context-aware automation triggered from OmniFocus UI
- Batch operations on multiple selected items

### 5. Create-If-Missing Pattern

**Pattern:** Elegantly handle creation of items that may or may not exist.

```javascript
// Create task only if it doesn't exist
const doc = Application('OmniFocus').defaultDocument;
const task = doc.taskNamed("Review proposal") || new Task("Review proposal");
```

**Lookup methods:**
- `taskNamed(name)` - Returns task or null if not found
- `projectNamed(name)` - Returns project or null if not found
- `tagNamed(name)` - Returns tag or null if not found

**Pattern explanation:**
- If item exists, returns the existing item
- If item doesn't exist (null), creates new item via `|| new Item(...)`
- Prevents duplicate creation
- Single-line idempotent operation

### 6. Smart Matching Functions

**Pattern:** Use intelligent matching for flexible item lookups.

Beyond exact name matching, OmniFocus provides smart matching that mimics the Quick Open window behavior:

```javascript
const doc = Application('OmniFocus').defaultDocument;

// Find tags matching pattern (fuzzy matching)
const urgentTags = doc.tagsMatching("urgent");

// Find projects matching pattern
const workProjects = doc.projectsMatching("work");

// Find folders matching pattern
const archiveFolders = doc.foldersMatching("archive");
```

**Benefits:**
- Fuzzy matching like Quick Open
- Finds items even with partial names
- More forgiving than exact name matching
- Returns arrays of matches

### 7. Positional Insertion

**Pattern:** Control where new items are inserted using positional indicators.

**Default behavior:**
```javascript
// Inserts at end by default
new Task("Task name");
```

**Positional insertion:**
```javascript
const doc = Application('OmniFocus').defaultDocument;

// Insert at beginning of inbox
new Task("Urgent task", doc.inbox.beginning);

// Insert at end of inbox (explicit)
new Task("Low priority", doc.inbox.end);

// Insert at beginning of a project
const project = doc.projectNamed("Work");
new Task("First task", project.beginning);
```

**Positional indicators:**
- `beginning` - Insert at start
- `end` - Insert at end
- `before(item)` - Insert before specific item
- `after(item)` - Insert after specific item

### 8. Data Persistence Pattern

**Critical:** Always save after modifications.

**Pattern:**
```javascript
// After any modification to OmniFocus data
this.save();
```

**Example:**
```javascript
(() => {
    const doc = Application('OmniFocus').defaultDocument;
    const task = new Task("New task");
    task.note = "Task details";
    task.flagged = true;

    // REQUIRED: Persist changes to database
    this.save();

    return "Task created";
})();
```

**Important notes:**
- Changes are not persisted until `save()` is called
- Always call after CREATE, UPDATE, or DELETE operations
- Call once at the end of script, not after every change
- Failure to save means changes are lost

### 9. Error Handling Pattern

**Pattern:** Wrap scripts in try-catch blocks for graceful error management.

```javascript
(() => {
    try {
        const doc = Application('OmniFocus').defaultDocument;
        // ... script logic ...
        this.save();
        return { success: true, message: "Operation completed" };
    } catch (error) {
        return { success: false, error: error.toString() };
    }
})();
```

**Benefits:**
- Prevents script crashes
- Provides useful error messages
- Enables debugging
- Allows graceful failure handling

### 10. Perspective Management

**Pattern:** Programmatically change views for context-appropriate displays.

```javascript
const doc = Application('OmniFocus').defaultDocument;
const win = doc.windows[0];

// Change to built-in perspective
win.perspective = Perspective.BuiltIn.Projects;
win.perspective = Perspective.BuiltIn.Forecast;
win.perspective = Perspective.BuiltIn.Flagged;

// Change to custom perspective by name
const customPerspective = doc.perspectiveNamed("My Custom View");
if (customPerspective) {
    win.perspective = customPerspective;
}
```

**Use cases:**
- Switch view after creating tasks
- Show relevant perspective for context
- Guide user attention to specific areas

## Conditional Task Processing

**Pattern:** Filter by task status for targeted operations.

```javascript
const doc = Application('OmniFocus').defaultDocument;
const tasks = doc.flattenedTasks();

// Filter by status
const availableTasks = tasks.filter(task =>
    task.taskStatus === Task.Status.Available
);

const completedTasks = tasks.filter(task =>
    task.taskStatus === Task.Status.Completed
);

const droppedTasks = tasks.filter(task =>
    task.taskStatus === Task.Status.Dropped
);
```

**Task statuses:**
- `Task.Status.Available` - Actionable tasks
- `Task.Status.Completed` - Completed tasks
- `Task.Status.Dropped` - Dropped/cancelled tasks
- `Task.Status.Blocked` - Blocked by dependencies

## Bulk Operations Pattern

**Pattern:** Combine iteration with conditional logic to process multiple items.

```javascript
(() => {
    const doc = Application('OmniFocus').defaultDocument;
    const tasks = doc.flattenedTasks();

    // Find all tasks starting with "Red"
    const redTasks = tasks.filter(task => task.name().startsWith("Red"));

    // Perform operation on each
    redTasks.forEach(task => {
        task.flagged = true;
    });

    this.save();
    return `Flagged ${redTasks.length} tasks`;
})();
```

## Comprehensive Hierarchical Search

**Pattern:** Search entire hierarchies before creating new items.

```javascript
const doc = Application('OmniFocus').defaultDocument;

// Search all projects (including nested)
const project = doc.flattenedProjects.byName("Project Name");

// Search all tags (including nested)
const tag = doc.flattenedTags.byName("Tag Name");

// Only create if not found
if (!project) {
    new Project("Project Name");
}
```

**byName() advantages:**
- Searches flattened hierarchies automatically
- No need for manual recursion
- Returns item or null
- Works with nested structures

## Object Model Key Points

### Containment Hierarchy

**Understanding what can contain what:**

- **Tags** - Can contain child Tags
- **Folders** - Can contain child Folders and Projects
- **Projects** - Can contain only Tasks (no sub-projects directly)
- **Tasks** - Can contain child Tasks (subtasks)

### Terminology Note

**UI vs API:**
- OmniFocus UI calls them **"Actions"**
- Scripts reference them as **"Tasks"**
- They are functionally synonymous
- Use "Task" in all script code

## Context Awareness

**Pattern:** Leverage implied context for cleaner code.

OmniFocus automation emphasizes implicit context. The database is directly referenceable without explicit hierarchy traversal:

```javascript
// Clean, context-aware code
(() => {
    const tasks = flattenedTasks(); // Implicit database context
    return tasks.length;
})();
```

This reduces verbosity while maintaining clarity about what's being accessed.

## Performance Considerations

### Use Flattened Collections for Searches

**Anti-pattern:**
```javascript
// Slow: Manual recursive search
function findTaskRecursively(tasks, name) {
    for (const task of tasks) {
        if (task.name() === name) return task;
        const found = findTaskRecursively(task.children, name);
        if (found) return found;
    }
    return null;
}
```

**Recommended:**
```javascript
// Fast: Use flattened collections
const doc = Application('OmniFocus').defaultDocument;
const task = doc.flattenedTasks.byName("Task Name");
```

### Batch Save Operations

**Anti-pattern:**
```javascript
// Inefficient: Save after every change
tasks.forEach(task => {
    task.flagged = true;
    this.save(); // DON'T DO THIS
});
```

**Recommended:**
```javascript
// Efficient: Save once at end
tasks.forEach(task => {
    task.flagged = true;
});
this.save(); // Single save for all changes
```

## Common Script Template

Combine best practices into a standard template:

```javascript
(() => {
    try {
        // Get database reference
        const doc = Application('OmniFocus').defaultDocument;

        // Access data using flattened collections
        const tasks = doc.flattenedTasks();

        // Filter for specific tasks
        const todayTasks = tasks.filter(task => {
            return task.taskStatus === Task.Status.Available &&
                   task.dueDate && isToday(task.dueDate());
        });

        // Perform operations
        todayTasks.forEach(task => {
            // Modify task properties
            task.flagged = true;
        });

        // Persist changes
        this.save();

        // Return success result
        return {
            success: true,
            message: `Flagged ${todayTasks.length} tasks due today`
        };

    } catch (error) {
        return {
            success: false,
            error: error.toString()
        };
    }
})();

function isToday(date) {
    const today = new Date();
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
}
```

## Script Organization

### Immediate Invocation Pattern

**Pattern:** Wrap scripts in immediately-invoked function expressions (IIFE).

```javascript
(() => {
    // Script logic here
    return result;
})();
```

**Benefits:**
- Creates clean scope
- Prevents variable pollution
- Returns result directly
- Standard OmniFocus plugin pattern

### Helper Functions

**Pattern:** Define helper functions outside IIFE, call from within.

```javascript
(() => {
    const doc = Application('OmniFocus').defaultDocument;
    const tasks = doc.flattenedTasks();

    const dueSoon = tasks.filter(task => isDueSoon(task, 7));

    return dueSoon.length;
})();

// Helper function defined separately
function isDueSoon(task, days) {
    if (!task.dueDate) return false;
    const dueDate = task.dueDate();
    const daysUntilDue = (dueDate - new Date()) / (1000 * 60 * 60 * 24);
    return daysUntilDue >= 0 && daysUntilDue <= days;
}
```

## Integration with Apple Intelligence

**New in OmniFocus 4.8+:** On-device AI capabilities via LanguageModel.Session.

See `foundation_models_integration.md` for complete documentation on:
- Natural language task processing
- Intelligent categorization
- Structured data extraction
- Smart task suggestions

**Quick example:**
```javascript
(async () => {
    const session = new LanguageModel.Session();
    const result = await session.respondWithSchema(
        "Categorize: Buy groceries and cook dinner",
        { type: "object", properties: { category: { type: "string" } } }
    );
    console.log(result.category); // "personal"
})();
```

## Summary of Key Patterns

1. **Database-centric** - Access database directly
2. **apply() vs forEach()** - Understand recursive vs flat iteration
3. **Flattened collections** - Use for efficient searching
4. **Selection-based** - Operate on user selections
5. **Create-if-missing** - `itemNamed() || new Item()`
6. **Smart matching** - Use tagsMatching(), projectsMatching()
7. **Positional insertion** - Control insertion points
8. **Always save** - Call `this.save()` after modifications
9. **Error handling** - Wrap in try-catch blocks
10. **Perspective management** - Programmatically change views

## External Resources

- **Official Omni Automation Reference:** [omni-automation.com/omnifocus/big-picture.html](https://omni-automation.com/omnifocus/big-picture.html)
- **Complete API Documentation:** See `OmniFocus-API.md` in this skill's references
- **Practical Examples:** See `workflows.md` for real-world automation patterns
- **Plugin Development:** See `omnifocus_plugin_structure.md` and `omnifocus_automation.md`
